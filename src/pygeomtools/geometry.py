"""Helper functions for geometry construction and manipulation."""

from __future__ import annotations

import warnings
from collections import Counter

import warnings
from collections import Counter

import logging

import awkward as ak
import legendhpges
import numpy as np
import pyg4ometry as pg4
from lgdo.types import VectorOfVectors
from numpy.typing import ArrayLike
from pyg4ometry import geant4

from pygeomtools import detectors

from .utils import _convert_positions, _get_matching_volumes

log = logging.getLogger(__name__)


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

        if float(mass) not in (0.0, 1.0):
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

def _is_inside_cylinder(points: ArrayLike, center: tuple, height: float, radius: float):
    """Check if 3 vectors are inside a cylinder"""
    z = points[:, 2]
    in_height = np.abs(z - center[2]) < height / 2.0
    dist = np.sqrt((points[:, 0] - center[0]) ** 2 + (points[:, 1] - center[1]) ** 2)
    in_radius = dist < radius

    return in_height & in_radius


def is_in_borehole(
    xloc: VectorOfVectors,
    yloc: VectorOfVectors,
    zloc: VectorOfVectors,
    reg: pg4.geant4.Registry,
    det: str | list[str] | None,
    unit: str = "mm",
    **kwargs
) -> VectorOfVectors:
    """Check which points are inside one or more borehole of the IC detectors.

    Parameters
    ----------
    xloc, yloc, zloc
        Arrays of positions. Note these should be the global coordinates.
    reg
        The geometry registry.
    detector
        One or more detector names to match. Can include wildcards.
    unit
        the unit for the positions
    **kwargs
        Additional keywords arguments to :func:`legendhpges.make_hpge`.
        
    Returns
    -------
    NDArray[bool]
        Boolean mask where True indicates the point is inside at least one borehole.
    """
    size, points = _convert_positions(xloc, yloc, zloc, unit=unit)

    inside = np.full(points.shape[0], False)

    det_list = _get_matching_volumes(list(reg.physicalVolumeDict.keys()), det)

    for det_tmp in det_list:
        # must have metadata in the registry for this to work
        meta = detectors.get_sensvol_metadata(reg, det_tmp)

        hpge = legendhpges.make_hpge(meta, registry=None, **kwargs)

        if not isinstance(hpge, legendhpges.InvertedCoax | legendhpges.V02160A | legendhpges.V07646A | legendhpges.V02162B):
            msg = f"Only InvertedCoaxial detectors have borehole not {hpge}"
            raise ValueError(msg)

        points_tmp = points - reg.physicalVolumeDict[det_tmp].position.eval()

        inside |= hpge.is_inside_borehole(points_tmp)

    return VectorOfVectors(ak.unflatten(inside, size))


def is_in_minishroud(
    xloc: VectorOfVectors,
    yloc: VectorOfVectors,
    zloc: VectorOfVectors,
    reg: pg4.geant4.Registry,
    unit: str = "mm",
    minishroud_pattern: str = "minishroud_*",
) -> VectorOfVectors:
    """Check which points are inside one or more NMS cylinders.

    Parameters
    ----------
    xloc, yloc, zloc
        Arrays of positions.
    reg
        The geometry registry.
    unit
        the unit for the positions
    minishroud_pattern
        a pattern to search for in the volume names.

    Returns
    -------
        VectorOfVectors of booleans where `True` indicates the point is inside at least one minishroud.

    """

    size, points = _convert_positions(xloc, yloc, zloc, unit=unit)

    inside = np.full(points.shape[0], False)

    string_list = _get_matching_volumes(
        list(reg.physicalVolumeDict.keys()), minishroud_pattern
    )

    for s in string_list:
        vol = reg.physicalVolumeDict[s]

        center = vol.position.eval()
        solid = vol.logicalVolume.solid

        if not isinstance(solid, pg4.geant4.solid.Subtraction):
            msg = f"Warning: {s} is not a subtraction solid"
            log.warning(msg)
            continue

        if not isinstance(solid.obj1, pg4.geant4.solid.Tubs):
            msg = f"Warning: {s} obj1 is not a G4Tubs"
            log.warning(msg)
            continue

        outer_ms = solid.obj1

        r_max = outer_ms.pRMax
        if isinstance(r_max, pg4.gdml.Defines.Expression):
            r_max = r_max.eval()

        dz = outer_ms.pDz
        if isinstance(dz, pg4.gdml.Defines.Quantity):
            dz = dz.eval()

        inside |= _is_inside_cylinder(points, center, dz, r_max)

    return VectorOfVectors(ak.unflatten(inside, size))
>>>>>>> add a method to check if a point is inside a minishroud
