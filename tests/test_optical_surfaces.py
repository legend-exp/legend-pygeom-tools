from __future__ import annotations

import warnings

import pyg4ometry.geant4 as g4
import pytest

from pygeomtools import RemageDetectorInfo
from pygeomtools.geometry import check_optical_surfaces


@pytest.fixture
def geom():
    """A world with a LAr mother volume and a Ge volume registered as optical detector."""
    reg = g4.Registry()
    world = g4.solid.Box("world", 2, 2, 2, reg, "m")
    world_lv = g4.LogicalVolume(
        world, g4.MaterialPredefined("G4_Galactic"), "world", reg
    )
    reg.setWorld(world_lv)

    scint = g4.solid.Box("scint", 0.5, 1, 1, reg, "m")
    scint_lv = g4.LogicalVolume(scint, g4.MaterialPredefined("G4_lAr"), "scint", reg)
    scint_pv = g4.PhysicalVolume([0, 0, 0], [0, 0, 0], scint_lv, "scint", world_lv, reg)

    det = g4.solid.Box("det", 0.1, 0.5, 0.5, reg, "m")
    det_lv = g4.LogicalVolume(det, g4.MaterialPredefined("G4_Ge"), "det", reg)
    det_pv = g4.PhysicalVolume([0, 0, 0], [0, 0, 0], det_lv, "det", scint_lv, reg)
    det_pv.pygeom_active_detector = RemageDetectorInfo("optical", 1)

    return reg, scint_pv, det_pv


def make_surface(
    reg,
    surf_type="dielectric_metal",
    *,
    efficiency=([1.0, 5.0], [0.2, 0.8]),
    reflectivity=([1.0, 5.0], [0.1, 0.5]),
    complex_rindex=False,
    name="os",
):
    osurf = g4.solid.OpticalSurface(name, "polished", "glisur", surf_type, 1.0, reg)
    if efficiency is not None:
        osurf.addVecProperty("EFFICIENCY", *efficiency)
    if reflectivity is not None:
        osurf.addVecProperty("REFLECTIVITY", *reflectivity)
    if complex_rindex:
        osurf.addVecProperty("REALRINDEX", [1.0, 5.0], [1.5, 1.5])
        osurf.addVecProperty("IMAGINARYRINDEX", [1.0, 5.0], [2.0, 2.0])
    return osurf


def assert_no_warning(reg):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        check_optical_surfaces(reg)


def test_border_surface_ok(geom):
    reg, scint_pv, det_pv = geom
    g4.BorderSurface("bs", scint_pv, det_pv, make_surface(reg), reg)
    assert_no_warning(reg)


def test_skin_surface_ok(geom):
    reg, _scint_pv, det_pv = geom
    g4.SkinSurface("sk", det_pv.logicalVolume, make_surface(reg), reg)
    assert_no_warning(reg)


def test_complex_rindex_ok(geom):
    reg, scint_pv, det_pv = geom
    surf = make_surface(reg, reflectivity=None, complex_rindex=True)
    g4.BorderSurface("bs", scint_pv, det_pv, surf, reg)
    assert_no_warning(reg)


def test_non_metal_no_reflectivity_ok(geom):
    reg, scint_pv, det_pv = geom
    surf = make_surface(reg, surf_type="dielectric_dielectric", reflectivity=None)
    g4.BorderSurface("bs", scint_pv, det_pv, surf, reg)
    assert_no_warning(reg)


def test_non_optical_detector_ignored(geom):
    reg, _scint_pv, det_pv = geom
    det_pv.pygeom_active_detector = RemageDetectorInfo("germanium", 1)
    assert_no_warning(reg)


def test_no_surface(geom):
    reg, _scint_pv, _det_pv = geom
    with pytest.warns(RuntimeWarning, match="no optical surface defined toward it"):
        check_optical_surfaces(reg)


def test_wrong_border_direction_not_counted(geom):
    reg, scint_pv, det_pv = geom
    # surface points away from the detector (det -> scint), so it does not count
    g4.BorderSurface("bs", det_pv, scint_pv, make_surface(reg), reg)
    with pytest.warns(RuntimeWarning, match="no optical surface defined toward it"):
        check_optical_surfaces(reg)


def test_multiple_surfaces(geom):
    reg, scint_pv, det_pv = geom
    g4.BorderSurface("bs", scint_pv, det_pv, make_surface(reg, name="os1"), reg)
    g4.SkinSurface("sk", det_pv.logicalVolume, make_surface(reg, name="os2"), reg)
    with pytest.warns(RuntimeWarning, match="more than one optical surface"):
        check_optical_surfaces(reg)


def test_no_efficiency(geom):
    reg, scint_pv, det_pv = geom
    surf = make_surface(reg, efficiency=None)
    g4.BorderSurface("bs", scint_pv, det_pv, surf, reg)
    with pytest.warns(RuntimeWarning, match="no EFFICIENCY set"):
        check_optical_surfaces(reg)


def test_zero_efficiency(geom):
    reg, scint_pv, det_pv = geom
    surf = make_surface(reg, efficiency=([1.0, 5.0], [0.0, 0.0]))
    g4.BorderSurface("bs", scint_pv, det_pv, surf, reg)
    with pytest.warns(RuntimeWarning, match="EFFICIENCY <= 0 at all points"):
        check_optical_surfaces(reg)


def test_metal_no_reflectivity_nor_rindex(geom):
    reg, scint_pv, det_pv = geom
    surf = make_surface(reg, reflectivity=None)
    g4.BorderSurface("bs", scint_pv, det_pv, surf, reg)
    with pytest.warns(RuntimeWarning, match="neither a REFLECTIVITY"):
        check_optical_surfaces(reg)


def test_metal_reflectivity_too_high(geom):
    reg, scint_pv, det_pv = geom
    surf = make_surface(reg, reflectivity=([1.0, 5.0], [1.0, 1.2]))
    g4.BorderSurface("bs", scint_pv, det_pv, surf, reg)
    with pytest.warns(RuntimeWarning, match="REFLECTIVITY >= 1 at all points"):
        check_optical_surfaces(reg)
