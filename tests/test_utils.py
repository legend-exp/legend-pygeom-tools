from __future__ import annotations

import awkward as ak
import numpy as np

from pygeomtools.utils import _convert_positions, _get_matching_volumes


def test_convert_positions():
    xloc = ak.Array([[1, 2], [1, 2, 3]])
    yloc = ak.Array([[1, 2], [1, 2, 3]])
    zloc = ak.Array([[1, 2], [1, 2, 3]])

    size, pos = _convert_positions(xloc, yloc, zloc, "mm")

    assert np.all(size == [2, 3])
    assert np.all(pos == [[1, 1, 1], [2, 2, 2], [1, 1, 1], [2, 2, 2], [3, 3, 3]])


def test_matching_patterns():
    vols = [
        "V012",
        "V103",
        "minishroud_string_1",
        "minishroud_string_2",
        "minishroud_string_3",
        "lar",
    ]

    assert _get_matching_volumes(vols, "V012") == ["V012"]
    assert _get_matching_volumes(vols, "V*") == ["V012", "V103"]
    assert _get_matching_volumes(vols, ["V*", "minishroud_string_1"]) == [
        "V012",
        "V103",
        "minishroud_string_1",
    ]
