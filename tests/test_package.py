from __future__ import annotations

import importlib.metadata

import pygeomtools


def test_package():
    assert importlib.metadata.version("legend-pygeom-tools") == pygeomtools.__version__
