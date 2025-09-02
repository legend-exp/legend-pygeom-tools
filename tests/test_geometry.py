from __future__ import annotations

import pyg4ometry.geant4 as g4
import pytest

from pygeomtools.geometry import check_materials


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
    reg, mat, e1, e2 = dummy_mat
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
