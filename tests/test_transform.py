from __future__ import annotations

import numpy as np
import pytest
from pyg4ometry import geant4 as g4

from pygeomtools.transform import get_global_extent, get_global_transform


@pytest.fixture
def nested_reg():
    registry = g4.Registry()
    vac = g4.MaterialPredefined("G4_Galactic")

    world = g4.solid.Box("world", 2, 2, 2, registry, "m")
    world_lv = g4.LogicalVolume(world, vac, "world", registry)
    registry.setWorld(world_lv)

    # mother: rotated by 90 deg around z, shifted along y.
    mother = g4.solid.Box("mother", 500, 500, 500, registry, "mm")
    mother_lv = g4.LogicalVolume(mother, vac, "mother", registry)
    g4.PhysicalVolume(
        [0, 0, np.pi / 2], [0, 100, 0], mother_lv, "mother", world_lv, registry
    )

    # daughter: unrotated, shifted along x in the mother frame.
    daughter = g4.solid.Box("daughter", 10, 20, 30, registry, "mm")
    daughter_lv = g4.LogicalVolume(daughter, vac, "daughter", registry)
    g4.PhysicalVolume(
        [0, 0, 0], [50, 0, 0], daughter_lv, "daughter", mother_lv, registry
    )

    # daughter of the daughter at its origin, rotated by 90 deg around x.
    inner = g4.solid.Box("inner", 2, 4, 6, registry, "mm")
    inner_lv = g4.LogicalVolume(inner, vac, "inner", registry)
    g4.PhysicalVolume(
        [np.pi / 2, 0, 0], [0, 0, 0], inner_lv, "inner", daughter_lv, registry
    )

    return registry


def test_global_transform_top_level(nested_reg):
    mtra, tra = get_global_transform(nested_reg, "mother")
    assert np.allclose(tra, [0, 100, 0])
    # GDML rotations are passive, i.e. local +x points to global -y.
    assert np.allclose(mtra @ [1, 0, 0], [0, -1, 0])


def test_global_transform_nested(nested_reg):
    mtra, tra = get_global_transform(nested_reg, "daughter")
    # the daughter offset gets rotated by the mother rotation.
    assert np.allclose(tra, [0, 50, 0])
    assert np.allclose(mtra @ [1, 0, 0], [0, -1, 0])

    # passing the object works the same as passing the name.
    pv = nested_reg.physicalVolumeDict["daughter"]
    mtra2, tra2 = get_global_transform(nested_reg, pv)
    assert np.allclose(mtra, mtra2)
    assert np.allclose(tra, tra2)


def test_global_extent(nested_reg):
    # unrotated, but placed in the world.
    ext = get_global_extent(nested_reg, "mother")
    assert np.allclose(ext, [[-250, -150, -250], [250, 350, 250]])

    # x and y half-lengths are swapped by the mother rotation.
    ext = get_global_extent(nested_reg, "daughter")
    assert np.allclose(ext, [[-10, 45, -15], [10, 55, 15]])

    # additionally, y and z half-lengths are swapped by the own rotation.
    ext = get_global_extent(nested_reg, "inner")
    assert np.allclose(ext, [[-3, 49, -2], [3, 51, 2]])


def test_global_extent_rotated_tight():
    registry = g4.Registry()
    vac = g4.MaterialPredefined("G4_Galactic")
    world_lv = g4.LogicalVolume(
        g4.solid.Box("world", 1, 1, 1, registry, "m"), vac, "world", registry
    )
    registry.setWorld(world_lv)

    box_lv = g4.LogicalVolume(
        g4.solid.Box("box", 10, 10, 10, registry, "mm"), vac, "box", registry
    )
    g4.PhysicalVolume([0, 0, np.pi / 4], [0, 0, 0], box_lv, "box", world_lv, registry)

    ext = get_global_extent(registry, "box")
    h = 5 * np.sqrt(2)
    assert np.allclose(ext, [[-h, -h, -5], [h, h, 5]])


def test_global_transform_assembly():
    registry = g4.Registry()
    vac = g4.MaterialPredefined("G4_Galactic")
    world_lv = g4.LogicalVolume(
        g4.solid.Box("world", 1, 1, 1, registry, "m"), vac, "world", registry
    )
    registry.setWorld(world_lv)

    assembly = g4.AssemblyVolume("assembly", registry)
    box_lv = g4.LogicalVolume(
        g4.solid.Box("box", 10, 10, 10, registry, "mm"), vac, "box", registry
    )
    g4.PhysicalVolume([0, 0, 0], [10, 0, 0], box_lv, "box", assembly, registry)
    g4.PhysicalVolume([0, 0, 0], [0, 0, 20], assembly, "assembly", world_lv, registry)

    _, tra = get_global_transform(registry, "box")
    assert np.allclose(tra, [10, 0, 20])

    with pytest.raises(TypeError):
        get_global_extent(registry, "assembly")


def test_global_transform_errors(nested_reg):
    with pytest.raises(ValueError, match="not found"):
        get_global_transform(nested_reg, "nonexistent")

    # PV that is not part of the world volume tree.
    vac = g4.MaterialPredefined("G4_Galactic")
    orphan_mother = g4.LogicalVolume(
        g4.solid.Box("orphan_mother", 1, 1, 1, nested_reg, "m"),
        vac,
        "orphan_mother",
        nested_reg,
    )
    orphan_lv = g4.LogicalVolume(
        g4.solid.Box("orphan", 1, 1, 1, nested_reg, "mm"), vac, "orphan", nested_reg
    )
    g4.PhysicalVolume(
        [0, 0, 0], [0, 0, 0], orphan_lv, "orphan", orphan_mother, nested_reg
    )
    with pytest.raises(ValueError, match="not placed"):
        get_global_transform(nested_reg, "orphan")

    # mother LV placed a second time makes the daughter position ambiguous.
    world_lv = nested_reg.worldVolume
    mother_lv = nested_reg.logicalVolumeDict["mother"]
    g4.PhysicalVolume(
        [0, 0, 0], [0, -600, 0], mother_lv, "mother2", world_lv, nested_reg
    )
    with pytest.raises(ValueError, match="ambiguous"):
        get_global_transform(nested_reg, "daughter")
    # the second placement itself is still unique.
    _, tra = get_global_transform(nested_reg, "mother2")
    assert np.allclose(tra, [0, -600, 0])
