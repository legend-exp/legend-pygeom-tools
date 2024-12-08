from __future__ import annotations

from . import detectors, geometry, utils
from ._version import version as __version__
from .detectors import RemageDetectorInfo, get_all_sensvols, get_sensvol_metadata

# note: do not load viewer module here, as it has quite large nested imports.

__all__ = [
    "RemageDetectorInfo",
    "__version__",
    "detectors",
    "geometry",
    "get_all_sensvols",
    "get_sensvol_metadata",
    "utils",
]
