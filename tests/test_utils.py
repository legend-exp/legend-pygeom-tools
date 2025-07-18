from __future__ import annotations

import awkward as ak
import numpy as np

from pygeomtools.utils import _convert_positions


def test_convert_positions():
    xloc = ak.Array([[1, 2], [1, 2, 3]])
    yloc = ak.Array([[1, 2], [1, 2, 3]])
    zloc = ak.Array([[1, 2], [1, 2, 3]])

    size, pos = _convert_positions(xloc, yloc, zloc, "mm")

    assert np.all(size == [2, 3])
    assert np.all(pos == [[1, 1, 1], [2, 2, 2], [1, 1, 1], [2, 2, 2], [3, 3, 3]])
