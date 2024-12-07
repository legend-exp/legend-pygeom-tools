from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Callable

import yaml
from legendmeta import AttrsDict

log = logging.getLogger(__name__)

__file_extensions__ = {"json": [".json"], "yaml": [".yaml", ".yml"]}


def load_dict(fname: str, ftype: str | None = None) -> dict:
    """Load a text file as a Python dict."""
    fname = Path(fname)

    # determine file type from extension
    if ftype is None:
        for _ftype, exts in __file_extensions__.items():
            if fname.suffix in exts:
                ftype = _ftype

    msg = f"loading {ftype} dict from: {fname}"
    log.debug(msg)

    with fname.open() as f:
        if ftype == "json":
            return json.load(f)
        if ftype == "yaml":
            return yaml.safe_load(f)

        msg = f"unsupported file format {ftype}"
        raise NotImplementedError(msg)


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
        return AttrsDict(load_dict(m))
    if isinstance(m, dict):
        return AttrsDict(m)
    return default()
