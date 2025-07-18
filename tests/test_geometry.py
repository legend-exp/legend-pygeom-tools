from __future__ import annotations

import awkward as ak
import numpy as np
import pyg4ometry as pg4
import pytest
from numpy import pi

from pygeomtools.geometry import _get_string_list, _is_inside_cylinder, is_in_minishroud


def test_is_inside_cylinder():
    # inside, outside vertically, outside horizontally
    points = np.array([[4, 3, 1.2], [0, 0, 0], [8, 0, 2]])

    is_in = _is_inside_cylinder(points, (0, 0, 2), 2, 6)

    assert np.all(is_in == [1, 0, 0])


@pytest.fixture
def test_make_geom():
    # create a world volume
    reg = pg4.geant4.Registry()

    world_s = pg4.geant4.solid.Orb("World_s", 20, registry=reg, lunit="cm")
    world_l = pg4.geant4.LogicalVolume(world_s, "G4_lAr", "World", registry=reg)
    reg.setWorld(world_l)

    # finally create a small radioactive source
    nms_out = pg4.geant4.solid.Tubs(
        "minishroud_outer",
        pRMin=0.0,
        pRMax=100.0,
        pDz=1000.0,
        pSPhi=0.0,
        pDPhi=2 * pi,
        lunit="mm",
        registry=reg,
    )
    nms_in = pg4.geant4.solid.Tubs(
        "minishroud_inner",
        pRMin=0.0,
        pRMax=99.0,
        pDz=1000.0,
        pSPhi=0,
        pDPhi=2 * pi,
        lunit="mm",
        registry=reg,
    )

    nms = pg4.geant4.solid.Subtraction(
        "minishroud", nms_out, nms_in, [[0, 0, 0], [0, 0, 0]], registry=reg
    )
    nms_l = pg4.geant4.LogicalVolume(nms, "G4_Fe", "minishroud", registry=reg)

    # place a few strings
    for string, x, y in zip([1, 2, 3, 4], [0, 50, 0, -50], [-50, 0, 50, 0]):
        pg4.geant4.PhysicalVolume(
            [0, 0, 0],
            [x, y, 0, "cm"],
            nms_l,
            f"minishroud_string_{string}",
            world_l,
            registry=reg,
        )

    return reg


def test_is_in_minishroud(test_make_geom):
    # create a world volume
    assert _get_string_list(test_make_geom, 1) == [1]
    assert _get_string_list(test_make_geom, [1, 2]) == [1, 2]
    assert _get_string_list(test_make_geom, None) == [1, 2, 3, 4]

    # place one point inside and one outside
    xloc = ak.Array([[0, 600]])
    yloc = ak.Array([[-450, 700]])
    zloc = ak.Array([[40, 100]])

    reg = test_make_geom
    # first point is in MS 1
    is_in = is_in_minishroud(xloc, yloc, zloc, reg, string=1).view_as("ak")
    assert ak.all(is_in == [[True, False]])

    is_in = is_in_minishroud(xloc, yloc, zloc, reg, string=None).view_as("ak")
    assert ak.all(is_in == [[True, False]])

    is_in = is_in_minishroud(xloc, yloc, zloc, reg, string=2).view_as("ak")
    assert ak.all(is_in == [[False, False]])
