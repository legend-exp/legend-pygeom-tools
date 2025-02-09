from __future__ import annotations

import logging
from typing import Callable

from dbetto import AttrsDict, utils

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
