from __future__ import annotations

import importlib.metadata

import pyg4ometry
from dbetto import AttrsDict
from pyg4ometry import geant4 as g4

import pygeomtools


def test_package():
    assert importlib.metadata.version("legend-pygeom-tools") == pygeomtools.__version__


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

    # test read again
    registry = pyg4ometry.gdml.Reader(tmp_path / "geometry.gdml").getRegistry()

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
