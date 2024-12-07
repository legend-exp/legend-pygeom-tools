"""Helper functions for geometry construction."""

from __future__ import annotations

from pyg4ometry import geant4


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
    if isinstance(v, (geant4.LogicalVolume, geant4.AssemblyVolume)):
        for dv in v.daughterVolumes:
            check_registry_sanity(dv, registry)
        check_registry_sanity(v.material, registry)
        check_registry_sanity(v.solid, registry)

    elif isinstance(v, geant4.PhysicalVolume):
        check_registry_sanity(v.logicalVolume, registry)

    elif isinstance(v, geant4.Registry):
        check_registry_sanity(v.worldVolume, registry)
        for _, s in v.surfaceDict.items():
            check_registry_sanity(s, registry)

    elif isinstance(v, geant4.Material):
        if hasattr(v, "components"):
            for comp in v.components:
                check_registry_sanity(comp[0], registry)

    elif isinstance(v, geant4.SurfaceBase):
        check_registry_sanity(v.surface_property, registry)

    elif isinstance(
        v, (geant4.solid.OpticalSurface, geant4.solid.SolidBase, geant4.Element)
    ):
        pass

    else:
        msg = f"invalid type {type(v)} encountered in check_registry_sanity volume tree"
        raise TypeError(msg)
