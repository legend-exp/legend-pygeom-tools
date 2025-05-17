from __future__ import annotations

import pyg4ometry
import pytest
from pyg4ometry import geant4 as g4


def test_vis_macro(tmp_path):
    from pygeomtools import visualization, write_pygeom

    registry = g4.Registry()
    world = g4.solid.Box("world", 2, 2, 2, registry, "m")
    world_lv = g4.LogicalVolume(
        world, g4.MaterialPredefined("G4_Galactic"), "world", registry
    )
    registry.setWorld(world_lv)

    scint = g4.solid.Box("scint", 0.5, 1, 1, registry, "m")
    scint1 = g4.LogicalVolume(
        scint, g4.MaterialPredefined("G4_lAr"), "scint1", registry
    )
    scint2 = g4.LogicalVolume(
        scint, g4.MaterialPredefined("G4_lAr"), "scint2", registry
    )
    g4.PhysicalVolume([0, 0, 0], [-255, 0, 0], scint1, "scint1", world_lv, registry)
    g4.PhysicalVolume([0, 0, 0], [+255, 0, 0], scint2, "scint2", world_lv, registry)
    scint1.pygeom_color_rgba = False
    scint2.pygeom_color_rgba = [1, 0, 1, 0.5]

    det = g4.solid.Box("det", 0.1, 0.5, 0.5, registry, "m")
    det = g4.LogicalVolume(det, g4.MaterialPredefined("G4_Ge"), "det", registry)
    g4.PhysicalVolume([0, 0, 0], [0, 0, 0], det, "det1", scint1, registry)
    det.pygeom_color_rgba = [0.3, 0, 1, 0.5]

    write_pygeom(registry, tmp_path / "geometry-vis.gdml")

    # test read again
    registry = pyg4ometry.gdml.Reader(tmp_path / "geometry-vis.gdml").getRegistry()

    visualization.load_color_auxvals_recursive(registry.worldVolume)

    assert not registry.logicalVolumeDict["scint1"].pygeom_color_rgba
    assert registry.logicalVolumeDict["scint2"].pygeom_color_rgba == [1, 0, 1, 0.5]
    assert registry.logicalVolumeDict["det"].pygeom_color_rgba == [0.3, 0, 1, 0.5]

    # test macro generation.
    visualization.generate_color_macro(registry, tmp_path / "color.mac")
    with (tmp_path / "color.mac").open() as f:
        generated_macro = f.read()

    expected_macro = """
/vis/geometry/set/forceSolid scint1
/vis/geometry/set/visibility scint1 -1 false
/vis/geometry/set/forceSolid det
/vis/geometry/set/colour det 0 0.3 0.0 1.0 0.5
/vis/geometry/set/forceSolid scint2
/vis/geometry/set/colour scint2 0 1.0 0.0 1.0 0.5
"""
    assert generated_macro.strip() == expected_macro.strip()


def test_double_write(tmp_path):
    from pygeomtools import visualization, write_pygeom

    registry = g4.Registry()
    world = g4.solid.Box("world", 2, 2, 2, registry, "m")
    world_lv = g4.LogicalVolume(
        world, g4.MaterialPredefined("G4_Galactic"), "world", registry
    )
    registry.setWorld(world_lv)

    scint = g4.solid.Box("scint", 0.5, 1, 1, registry, "m")
    scint1 = g4.LogicalVolume(
        scint, g4.MaterialPredefined("G4_lAr"), "scint1", registry
    )
    scint2 = g4.LogicalVolume(
        scint, g4.MaterialPredefined("G4_lAr"), "scint2", registry
    )
    g4.PhysicalVolume([0, 0, 0], [-255, 0, 0], scint1, "scint1", world_lv, registry)
    g4.PhysicalVolume([0, 0, 0], [+255, 0, 0], scint2, "scint2", world_lv, registry)
    scint1.pygeom_color_rgba = False
    scint2.pygeom_color_rgba = [1, 0, 1, 0.5]

    write_pygeom(registry, tmp_path / "geometry-vis.gdml")

    # simulate a second write
    registry.userInfo = []
    write_pygeom(registry, tmp_path / "geometry-vis.gdml")

    # test read again
    registry = pyg4ometry.gdml.Reader(tmp_path / "geometry-vis.gdml").getRegistry()

    visualization.load_color_auxvals_recursive(registry.worldVolume)


def test_vis_typo(tmp_path):
    from pygeomtools import write_pygeom

    registry = g4.Registry()
    world = g4.solid.Box("world", 2, 2, 2, registry, "m")
    world_lv = g4.LogicalVolume(
        world, g4.MaterialPredefined("G4_Galactic"), "world", registry
    )
    registry.setWorld(world_lv)

    scint = g4.solid.Box("scint", 0.5, 1, 1, registry, "m")
    scint1 = g4.LogicalVolume(scint, g4.MaterialPredefined("G4_lAr"), "scint", registry)
    g4.PhysicalVolume([0, 0, 0], [-255, 0, 0], scint1, "scint", world_lv, registry)
    scint1.pygeom_colour_rgba = False

    with pytest.raises(RuntimeError, match="use use pygeom_color_rgba instead"):
        write_pygeom(registry, tmp_path / "geometry-vis2.gdml")
