from __future__ import annotations

import fnmatch
import logging
from collections.abc import Callable

import awkward as ak
import numpy as np
from dbetto import AttrsDict, utils
from lgdo.types import VectorOfVectors
from numpy.typing import NDArray

log = logging.getLogger(__name__)


def load_dict(fname: str, ftype: str | None = None) -> dict:
    """Load a text file as a Python dict.

    .. deprecated :: 0.0.8
        Use :func:`dbetto.utils.load_dict` instead.
    """
    import warnings

    warnings.warn(
        "The load_dict function has moved to the dbetto package (https://github.com/gipert/dbetto). "
        "Please update your code, as load_dict will be removed from this package in the future.",
        DeprecationWarning,
        stacklevel=2,
    )

    return utils.load_dict(fname, ftype)


def load_dict_from_config(
    config: dict, key: str, default: Callable[[], AttrsDict]
) -> AttrsDict:
    """Helper functions to load nested data from a config file.

    * If ``key`` is in the config file
      - and it refers to a string: load a JSON/YAML file from that path.
      - and it refers to a dict: use that directly
    * else, the default value is loaded via the ``default`` callable.
    """
    m = config.get(key)
    if isinstance(m, str):
        return AttrsDict(utils.load_dict(m))
    if isinstance(m, dict):
        return AttrsDict(m)
    return default()


def _convert_positions(
    xloc: VectorOfVectors, yloc: VectorOfVectors, zloc: VectorOfVectors, unit: str
) -> tuple[NDArray, NDArray]:
    """Convert vector of vectors into a flat array of 3 vector positions."""
    # Normalize string input to list
    factor = np.array([1, 100, 1000])[unit == np.array(["mm", "cm", "m"])][0]

    pos = []
    sizes = []

    for pos_tmp in [xloc, yloc, zloc]:
        local_pos_tmp = ak.Array(pos_tmp) * factor
        local_pos_flat_tmp = ak.flatten(local_pos_tmp).to_numpy()
        pos.append(local_pos_flat_tmp)
        sizes.append(ak.num(local_pos_tmp, axis=1))

    if not ak.all(sizes[0] == sizes[1]) or not ak.all(sizes[0] == sizes[2]):
        msg = "all position vector of vector must have the same shape"
        raise ValueError(msg)

    size = sizes[0]

    # restructure the positions
    local_positions = np.vstack(pos).T
    return size, local_positions


def _get_matching_volumes(volume_list: list, patterns: str | list) -> list[int]:
    """Get the list of volumes from the GDML. The string can include wildcards."""

    wildcard_list = [patterns] if isinstance(patterns, str) else patterns

    # find all volumes matching at least one pattern
    matched_list = []
    for key in volume_list:
        for name in wildcard_list:
            if fnmatch.fnmatch(key, name):
                matched_list.append(key)
    return matched_list
