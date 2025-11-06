"""Helper functions for geometry construction."""

from __future__ import annotations

import re
import warnings
from collections import Counter
from typing import Literal

import numpy as np
import pint
import pyg4ometry.geant4 as g4
from pyg4ometry import geant4

from . import detectors

u = pint.get_application_registry()


def check_registry_sanity(v, registry: geant4.Registry) -> None:
    """Check recursively if all children in the volume and material tree have the correct
    registry instance attached.

    Parameters
    ==========
    v
        object to recursively check to have the right registry.
    registry
        the expected registry to compare against

    Note
    ====
    This function prevents an easy-to-miss problem using pyg4ometry: If different (or no)
    registries are used inside an object structure, this might lead to unexpected results
    in GDML output.
    """
    if not isinstance(v, geant4.Registry) and v.registry is not registry:
        msg = f"found invalid registry instance on {v}"
        raise RuntimeError(msg)

    # Geant4 has some weird behavior if the name is a valid GDML expression, so just allow
    # a limited set of characters here.
    if isinstance(v, geant4.LogicalVolume | geant4.PhysicalVolume) and not re.match(
        "^[a-zA-Z0-9._-]+$", v.name
    ):
        msg = f"invalid name {v.name} for {type(v)}"
        raise RuntimeError(msg)

    # walk the tree.
    if isinstance(v, geant4.LogicalVolume | geant4.AssemblyVolume):
        for dv in v.daughterVolumes:
            check_registry_sanity(dv, registry)
        check_registry_sanity(v.material, registry)
        check_registry_sanity(v.solid, registry)

    elif isinstance(v, geant4.PhysicalVolume):
        check_registry_sanity(v.logicalVolume, registry)

    elif isinstance(v, geant4.Registry):
        check_registry_sanity(v.worldVolume, registry)
        for s in v.surfaceDict.values():
            check_registry_sanity(s, registry)

        check_materials(registry)

    elif isinstance(v, geant4.Material):
        if hasattr(v, "components"):
            for comp in v.components:
                check_registry_sanity(comp[0], registry)
            if v not in registry.materialDict.values():
                warnings.warn(
                    f"found material {v.name} not in materialDict",
                    RuntimeWarning,
                    stacklevel=1,
                )

    elif isinstance(v, geant4.SurfaceBase):
        check_registry_sanity(v.surface_property, registry)

    elif isinstance(
        v, geant4.solid.OpticalSurface | geant4.solid.SolidBase | geant4.Element
    ):
        pass

    else:
        msg = f"invalid type {type(v)} encountered in check_registry_sanity volume tree"
        raise TypeError(msg)


def check_materials(registry: geant4.Registry) -> None:
    """Check against some common problems of materials."""
    for mat in registry.materialDict.values():
        if not hasattr(mat, "components"):
            continue

        elems = []
        mass = 0
        types = set()
        for comp in mat.components:
            elems.append(comp[0].name)
            mass += comp[1] if comp[2] == "massfraction" else 0
            types.add(comp[2])

        duplicate_elems = [elem for elem, count in Counter(elems).items() if count > 1]
        if duplicate_elems != []:
            warnings.warn(
                f"Material {mat.name} with duplicate elements {duplicate_elems}",
                RuntimeWarning,
                stacklevel=1,
            )

        if not np.isclose(mass, 0.0) and not np.isclose(mass, 1.0):
            warnings.warn(
                f"Material {mat.name} with invalid massfraction sum {mass:.3f}",
                RuntimeWarning,
                stacklevel=1,
            )

        if (
            len(types) > 1
            and not isinstance(mat, geant4._Material.Element)
            and not mat.name.startswith("G4")
        ):
            warnings.warn(
                f"Material {mat.name} with component type mixture",
                RuntimeWarning,
                stacklevel=1,
            )


def get_approximate_volume(lv: geant4.LogicalVolume) -> pint.Quantity:
    """Get the cubic volume of the logical volume, subtracting the cubic volumes of the
    daughter volumes.

    .. note::
        The result is not an exact number, but is based on the mesh calculated internally
        by pyg4ometry. By using :func:`pyg4ometry.config.setGlobalMeshSliceAndStack`
        before loading or creating the geometry, you can adjust how fine the mesh will be.
    """
    vol = lv.solid.mesh().volume()
    for pv in lv.daughterVolumes:
        vol -= pv.logicalVolume.solid.mesh().volume()
    assert vol >= 0

    return (vol * u("mm**3")).to("m**3")


def print_volumes(
    registry: g4.Registry,
    which: Literal["logical" | "physical" | "detector"],
    include_volume: bool = False,
) -> None:
    """Print details about volume registered in the registry.

    Parameters
    ==========
    which
        the type of volumes to print. Can be `logical`, `physical` or `detector`, to
        print details about logical volumes, physical volumes or remage detector
        registrations.
    include_volume
        if listing logical volumes, include the approximate volume as determined with
        :func:`get_approximate_volume`.
    """
    import pandas as pd

    lines = []
    if which == "logical":
        for name, lv in registry.logicalVolumeDict.items():
            solid = lv.solid
            solid_type = (
                solid.__class__.__name__ if solid is not None else "UnknownSolid"
            )
            material = lv.material
            mat_name = getattr(material, "name", "UnknownMaterial")
            density = getattr(material, "density", "UnknownDensity")
            line = {
                "name": name,
                "solid": solid_type,
                "material": mat_name,
                "density [g/cm3]": density,
            }
            if include_volume:
                line["approx. volume"] = get_approximate_volume(lv)
            lines.append(line)
    elif which == "physical":
        for name, pv in registry.physicalVolumeDict.items():
            copy_nr = pv.copyNumber
            lv = pv.logicalVolume
            lv_name = lv if isinstance(lv, str) else getattr(lv, "name", "?")
            lines.append({"name": name, "copy_nr": copy_nr, "logical": lv_name})
    elif which == "detector":
        for pv, det in detectors.walk_detectors(registry.worldVolume):
            lines.append({"name": pv.name, "uid": det.uid, "type": det.detector_type})
    else:
        msg = f"unknown volume type {which}"
        raise ValueError(msg)

    table = pd.DataFrame.from_dict(lines).set_index("name").sort_index()
    print(table.to_string())  # noqa: T201
