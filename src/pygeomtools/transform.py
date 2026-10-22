"""Helper functions to obtain global transformations and extents of volumes."""

from __future__ import annotations

import numpy as np
from pyg4ometry import geant4, transformation


def _find_pv_paths(
    reg: geant4.Registry, pv: geant4.PhysicalVolume
) -> list[list[geant4.PhysicalVolume]]:
    """Find all placement paths (from the world volume down to `pv`) in the volume tree."""
    paths = []

    def _walk(v, *path) -> None:
        if isinstance(v, geant4.LogicalVolume | geant4.AssemblyVolume):
            for dv in v.daughterVolumes:
                _walk(dv, *path)  # LVs do not contribute to path.
        elif isinstance(v, geant4.PhysicalVolume):
            if v is pv:
                paths.append([*path, v])
            else:
                _walk(v.logicalVolume, *path, v)
        else:
            msg = f"invalid type {type(v)} encountered in volume tree"
            raise TypeError(msg)

    _walk(reg.worldVolume)
    return paths


def get_global_transform(
    reg: geant4.Registry, pv: str | geant4.PhysicalVolume
) -> tuple[np.ndarray, np.ndarray]:
    """Get the transformation of a physical volume relative to the world volume.

    The returned transformation maps a point ``x`` in the local coordinate system of
    the physical volume's logical volume to the global coordinate ``mtra @ x + tra``.

    Parameters
    ==========
    reg
        the registry containing the volume tree.
    pv
        the physical volume (or its name) to get the transformation for.

    Returns
    =======
    a tuple ``(mtra, tra)`` of the global 3x3 rotation (and scaling) matrix and the
    global translation vector.
    """
    if isinstance(pv, str):
        if pv not in reg.physicalVolumeDict:
            msg = f"physical volume {pv} not found"
            raise ValueError(msg)
        pv = reg.physicalVolumeDict[pv]

    paths = _find_pv_paths(reg, pv)
    if len(paths) == 0:
        msg = f"physical volume {pv.name} is not placed in the world volume tree"
        raise ValueError(msg)
    if len(paths) > 1:
        msg = (
            f"physical volume {pv.name} is placed {len(paths)} times in the world "
            "volume tree, the global transformation is ambiguous"
        )
        raise ValueError(msg)

    # derived from pyg4ometry's ViewerBase.
    mtra = np.identity(3)
    tra = np.zeros(3)
    for p in paths[0]:
        if p.type != "placement":
            msg = f"unsupported physical volume type {p.type} of {p.name}"
            raise NotImplementedError(msg)

        pvmrot = np.linalg.inv(transformation.tbxyz2matrix(p.rotation.eval()))
        pvmsca = np.diag(p.scale.eval()) if p.scale else np.identity(3)
        pvtra = np.array(p.position.eval())

        mtra, tra = mtra @ pvmrot @ pvmsca, mtra @ pvtra + tra

    return mtra, tra


def get_global_extent(
    reg: geant4.Registry, pv: str | geant4.PhysicalVolume
) -> np.ndarray:
    """Get the axis-aligned (approximate) bounding box of a physical volume in global
    coordinates.

    The bounding box is computed from the transformed mesh vertices of the volume's
    solid, i.e. it is tight even for rotated volumes. Daughter volumes are not
    considered. For round volumes, the mesh might be smaller than the analytical
    description of the volume.

    Parameters
    ==========
    reg
        the registry containing the volume tree.
    pv
        the physical volume (or its name) to get the extent for.

    Returns
    =======
    an array of shape ``(2, 3)`` with the minimum and maximum corners of the bounding
    box, in the default length unit (mm).
    """
    if isinstance(pv, str):
        if pv not in reg.physicalVolumeDict:
            msg = f"physical volume {pv} not found"
            raise ValueError(msg)
        pv = reg.physicalVolumeDict[pv]

    lv = pv.logicalVolume
    if not isinstance(lv, geant4.LogicalVolume):
        msg = f"cannot compute extent of {pv.name} with type {type(lv)}"
        raise TypeError(msg)
    if getattr(lv, 'mesh', None) is None:
        msg = f"logical volume {lv.name} has no mesh"
        raise RuntimeError(msg)

    mtra, tra = get_global_transform(reg, pv)

    vertices, _, _ = lv.mesh.localmesh.toVerticesAndPolygons()
    vertices = np.vstack(vertices) @ mtra.T + tra

    return np.array([vertices.min(axis=0), vertices.max(axis=0)])
