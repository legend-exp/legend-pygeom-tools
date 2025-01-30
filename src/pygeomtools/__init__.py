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
    "visualization",
    "write_pygeom",
]
