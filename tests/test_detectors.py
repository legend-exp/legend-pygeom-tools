from __future__ import annotations

import pyg4ometry
import pytest
from dbetto import AttrsDict
from pyg4ometry import geant4 as g4


def test_detector_info(tmp_path):
    from pygeomtools import RemageDetectorInfo, detectors, write_pygeom

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
    scint1pv = g4.PhysicalVolume(
        [0, 0, 0], [-255, 0, 0], scint1, "scint1", world_lv, registry
    )
    scint1pv.set_pygeom_active_detector(RemageDetectorInfo("scintillator", 3))
    scint2pv = g4.PhysicalVolume(
        [0, 0, 0], [+255, 0, 0], scint2, "scint2", world_lv, registry
    )
    assert scint2pv.get_pygeom_active_detector() is None
    scint2pv.set_pygeom_active_detector(RemageDetectorInfo("scintillator", 3))
    assert scint2pv.pygeom_active_detector is not None
    assert scint2pv.get_pygeom_active_detector() == scint2pv.pygeom_active_detector

    det = g4.solid.Box("det", 0.1, 0.5, 0.5, registry, "m")
    det = g4.LogicalVolume(det, g4.MaterialPredefined("G4_Ge"), "det", registry)
    det1 = g4.PhysicalVolume([0, 0, 0], [0, 0, 0], det, "det1", scint1, registry)
    det1.pygeom_active_detector = RemageDetectorInfo("optical", 1, {"some": "metadata"})
    det2 = g4.PhysicalVolume([0, 0, 0], [0, 0, 0], det, "det2", scint2, registry)
    det2.pygeom_active_detector = RemageDetectorInfo(
        "germanium", 2, {"other": "other metadata"}
    )

    write_pygeom(registry, tmp_path / "geometry.gdml")
    detectors.generate_detector_macro(registry, tmp_path / "geometry.mac")
    expected_macro = """
/RMG/Geometry/RegisterDetector Germanium det2 2
/RMG/Geometry/RegisterDetector Optical det1 1
/RMG/Geometry/RegisterDetector Scintillator scint1 3
/RMG/Geometry/RegisterDetector Scintillator scint2 3
"""
    assert (tmp_path / "geometry.mac").read_text().strip() == expected_macro.strip()

    # test read again
    registry = pyg4ometry.gdml.Reader(tmp_path / "geometry.gdml").getRegistry()

    all_top_level_aux = [(aux.auxtype, aux.auxvalue) for aux in registry.userInfo]
    assert all_top_level_aux == [
        ("RMG_detector_meta", ""),
        ("RMG_detector", "germanium"),
        ("RMG_detector", "optical"),
        ("RMG_detector", "scintillator"),
    ]

    # test that our API functions work.
    assert detectors.get_sensvol_metadata(registry, "det2") == {
        "other": "other metadata"
    }
    det1meta = detectors.get_sensvol_metadata(registry, "det1")
    assert det1meta == {"some": "metadata"}
    assert det1meta.some == "metadata"
    assert isinstance(det1meta, AttrsDict)
    assert detectors.get_sensvol_metadata(registry, "scint1") is None
    sensvols = detectors.get_all_sensvols(registry)
    assert set(sensvols.keys()) == {"det2", "det1", "scint1", "scint2"}
    assert sensvols["scint1"].uid == 3

    # test retrieval by uid.
    assert detectors.get_sensvol_by_uid(registry, 3) == ("scint1", sensvols["scint1"])
    assert detectors.get_sensvol_by_uid(registry, 5) is None


def test_detector_typo(tmp_path):
    from pygeomtools import RemageDetectorInfo, detectors, write_pygeom

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
    scint1pv = g4.PhysicalVolume(
        [0, 0, 0], [-255, 0, 0], scint1, "scint1", world_lv, registry
    )
    with pytest.deprecated_call():
        scint1pv.pygeom_active_dector = RemageDetectorInfo("scintillator", 3)
    assert scint1pv.get_pygeom_active_detector() is not None
    assert scint1pv.pygeom_active_detector is not None
    with pytest.deprecated_call():
        assert scint1pv.pygeom_active_dector is not None

    write_pygeom(registry, tmp_path / "geometry_typo.gdml")

    # test read again
    registry = pyg4ometry.gdml.Reader(tmp_path / "geometry_typo.gdml").getRegistry()

    all_top_level_aux = [(aux.auxtype, aux.auxvalue) for aux in registry.userInfo]
    assert all_top_level_aux == [
        ("RMG_detector_meta", ""),
        ("RMG_detector", "scintillator"),
    ]

    sensvols = detectors.get_all_sensvols(registry)
    assert set(sensvols.keys()) == {"scint1"}
    assert sensvols["scint1"].uid == 3
    assert detectors.get_sensvol_by_uid(registry, 3) == ("scint1", sensvols["scint1"])


def test_no_detector_info(tmp_path):
    from pygeomtools import detectors, write_pygeom

    registry = g4.Registry()
    world = g4.solid.Box("world", 2, 2, 2, registry, "m")
    world_lv = g4.LogicalVolume(
        world, g4.MaterialPredefined("G4_Galactic"), "world", registry
    )
    registry.setWorld(world_lv)

    scint = g4.solid.Box("scint", 0.5, 1, 1, registry, "m")
    scint = g4.LogicalVolume(scint, g4.MaterialPredefined("G4_lAr"), "scint1", registry)
    g4.PhysicalVolume([0, 0, 0], [-255, 0, 0], scint, "scint1", world_lv, registry)

    write_pygeom(registry, tmp_path / "geometry_no_det.gdml")
    detectors.generate_detector_macro(registry, tmp_path / "geometry_no_det.mac")
    assert (tmp_path / "geometry_no_det.mac").read_text() == ""

    # test read again
    registry = pyg4ometry.gdml.Reader(tmp_path / "geometry_no_det.gdml").getRegistry()
    assert detectors.get_sensvol_metadata(registry, "det1") is None

    all_top_level_aux = [(aux.auxtype, aux.auxvalue) for aux in registry.userInfo]
    assert all_top_level_aux == [("RMG_detector_meta", "")]
    assert registry.userInfo[0].subaux == []


def test_wrong_write(tmp_path):
    from pygeomtools import detectors

    registry = g4.Registry()
    world = g4.solid.Box("world", 2, 2, 2, registry, "m")
    world_lv = g4.LogicalVolume(
        world, g4.MaterialPredefined("G4_Galactic"), "world", registry
    )
    registry.setWorld(world_lv)

    scint = g4.solid.Box("scint", 0.5, 1, 1, registry, "m")
    scint = g4.LogicalVolume(scint, g4.MaterialPredefined("G4_lAr"), "scint1", registry)
    g4.PhysicalVolume([0, 0, 0], [-255, 0, 0], scint, "scint1", world_lv, registry)

    w = pyg4ometry.gdml.Writer()
    w.addDetector(registry)
    w.write(str(tmp_path / "geometry_wrong_write.gdml"))

    # test read again
    registry = pyg4ometry.gdml.Reader(
        tmp_path / "geometry_wrong_write.gdml"
    ).getRegistry()
    with pytest.raises(RuntimeError):
        detectors.get_sensvol_metadata(registry, "det1")
    with pytest.raises(RuntimeError):
        detectors.get_all_sensvols(registry)
    with pytest.raises(RuntimeError):
        detectors.get_sensvol_by_uid(registry, 5)

    all_top_level_aux = [(aux.auxtype, aux.auxvalue) for aux in registry.userInfo]
    assert all_top_level_aux == []
