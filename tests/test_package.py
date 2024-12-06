from __future__ import annotations

import importlib.metadata

import pygeomtools as m


def test_package():
    assert importlib.metadata.version("legend-pygeom-tools") == m.__version__
