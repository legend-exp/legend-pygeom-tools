from __future__ import annotations

import numpy as np
import pyg4ometry.geant4 as g4
import pytest

from pygeomtools.geometry import check_materials, get_approximate_volume


@pytest.fixture
def dummy_mat():
    reg = g4.Registry()
    mat = g4.Material(name="m", density=1, number_of_components=2, registry=reg)
    e1 = g4.ElementSimple(name="E1", symbol="E1", Z=1, A=1, registry=reg)
    e2 = g4.ElementSimple(name="E2", symbol="E2", Z=1, A=2, registry=reg)
    return reg, mat, e1, e2


def test_material_normal(dummy_mat):
    reg, mat, e1, e2 = dummy_mat
    mat.add_element_massfraction(e1, massfraction=0.2)
    mat.add_element_massfraction(e2, massfraction=0.8)
    check_materials(reg)


def test_material_wrong_sum(dummy_mat):
    reg, mat, e1, e2 = dummy_mat
    mat.add_element_massfraction(e1, massfraction=0.2)
    mat.add_element_massfraction(e2, massfraction=0.7)

    with pytest.warns(RuntimeWarning, match="massfraction"):
        check_materials(reg)


def test_material_duplicate_element(dummy_mat):
    reg, mat, e1, _e2 = dummy_mat
    mat.add_element_massfraction(e1, massfraction=0.2)
    mat.add_element_massfraction(e1, massfraction=0.8)

    with pytest.warns(RuntimeWarning, match="duplicate elements"):
        check_materials(reg)


def test_material_component_mixture(dummy_mat):
    reg, mat, e1, e2 = dummy_mat
    mat.add_element_massfraction(e1, massfraction=0.2)
    mat.add_element_natoms(e2, natoms=2)

    with pytest.warns(RuntimeWarning) as record:
        check_materials(reg)
    assert len(record) == 2
    assert str(record[0].message) == "Material m with invalid massfraction sum 0.200"
    assert str(record[1].message) == "Material m with component type mixture"


def test_approximate_volume():
    registry = g4.Registry()
    world = g4.solid.Box("world", 2, 2, 2, registry, "m")
    world_lv = g4.LogicalVolume(
        world, g4.MaterialPredefined("G4_Galactic"), "world", registry
    )
    registry.setWorld(world_lv)

    lar_mat = g4.MaterialPredefined("G4_lAr")
    scint = g4.solid.Box("scint", 0.5, 1, 1, registry, "m")
    scint1 = g4.LogicalVolume(scint, lar_mat, "scint1", registry)
    g4.PhysicalVolume([0, 0, 0], [-255, 0, 0], scint1, "scint1", world_lv, registry)

    det = g4.solid.Box("det", 0.1, 0.5, 0.5, registry, "m")
    det = g4.LogicalVolume(det, g4.MaterialPredefined("G4_Ge"), "det", registry)
    g4.PhysicalVolume([0, 0, 0], [0, 0, 0], det, "det1", scint1, registry)

    assert np.isclose(get_approximate_volume(det).m, 0.1 * 0.5 * 0.5)
    assert np.isclose(get_approximate_volume(scint1).m, 0.5 - (0.1 * 0.5 * 0.5))
