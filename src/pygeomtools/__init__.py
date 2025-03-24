from __future__ import annotations

# note: do not load viewer module here, as it has quite large nested imports. see lazy loading below.
from . import detectors, geometry, utils, visualization
from ._version import version as __version__
from .detectors import RemageDetectorInfo, get_all_sensvols, get_sensvol_metadata
from .write import write_pygeom

__all__ = [
    "RemageDetectorInfo",
    "__version__",
    "detectors",
    "geometry",
    "get_all_sensvols",
    "get_sensvol_metadata",
    "utils",
    "viewer",  # lazy import!
    "visualization",
    "write_pygeom",
]


# inspired by PEP 562.
def __getattr__(name: str):
    if name in __all__:
        import importlib

        return importlib.import_module(f".{name}", __name__)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
