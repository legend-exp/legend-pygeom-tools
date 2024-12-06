from __future__ import annotations

import importlib.metadata

import legend_pygeom_tools as m


def test_version():
    assert importlib.metadata.version("legend_pygeom_tools") == m.__version__
