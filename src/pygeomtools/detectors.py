"""Assignment of sensitive detectors to physical volumes, for use in ``remage``."""

from __future__ import annotations

import json
import logging
from collections.abc import Generator
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path
from typing import Literal

import pyg4ometry.geant4 as g4
from pyg4ometry.gdml.Defines import Auxiliary

log = logging.getLogger(__name__)


@dataclass
class RemageDetectorInfo:
    detector_type: Literal["optical", "germanium", "scintillator"]
    """``remage`` detector type."""

    uid: int
    """``remage`` detector UID."""

    metadata: object | None = None
    """Attach arbitrary metadata to this sensitive volume. This will be written to GDML as JSON.

    See also
    ========
    .get_sensvol_metadata
    """


def walk_detectors(
    pv: g4.PhysicalVolume | g4.LogicalVolume | g4.Registry,
) -> Generator[tuple[g4.PhysicalVolume, RemageDetectorInfo], None, None]:
    """Iterate over all physical volumes that have a :class:`RemageDetectorInfo` attached."""

    if isinstance(pv, g4.PhysicalVolume) and hasattr(pv, "pygeom_active_dector"):
        det = pv.pygeom_active_dector
        assert isinstance(det, RemageDetectorInfo)
        yield pv, det

    if isinstance(pv, g4.LogicalVolume):
        next_v = pv
    if isinstance(pv, g4.PhysicalVolume):
        next_v = pv.logicalVolume
    elif isinstance(pv, g4.Registry):
        next_v = pv.worldVolume
    else:
        msg = "invalid type encountered in walk_detectors volume tree"
        raise TypeError(msg)

    for dv in next_v.daughterVolumes:
        if dv.type == "placement":
            yield from walk_detectors(dv)


def generate_detector_macro(registry: g4.Registry, filename: str) -> None:
    """Create a Geant4 macro file containing the defined active detector volumes for use in remage."""

    macro_lines = {}

    for pv, det in walk_detectors(registry):
        if pv.name in macro_lines:
            return
        mac = f"/RMG/Geometry/RegisterDetector {det.detector_type.title()} {pv.name} {det.uid}\n"
        macro_lines[pv.name] = mac

    macro_contents = "".join(macro_lines.values())

    with Path.open(filename, "w", encoding="utf-8") as f:
        f.write(macro_contents)


def write_detector_auxvals(registry: g4.Registry) -> None:
    """Append an auxiliary structure, storing the sensitive detector volume information.

    The structure is a nested dict, stored as follows (read ``auxtype`: ``auxvalue``):

    * "RMG_detector": ``det_type`` (see :class:`RemageDetectorInfo`)
        * ``physvol->name``: ``det_uid``
        * [...repeat...]
    * [...repeat...]
    * "RMG_detector_meta": ""
        * ``physvol->name``: ``json(metadata)``
        * [...repeat...]
    """

    written_pvs = set()
    group_it = groupby(walk_detectors(registry), lambda d: d[1].detector_type)

    meta_group_aux = Auxiliary("RMG_detector_meta", "", registry)

    for key, group in group_it:
        group_aux = Auxiliary("RMG_detector", key, registry)

        for pv, det in group:
            if pv.name in written_pvs:
                return
            written_pvs.add(pv.name)

            group_aux.addSubAuxiliary(
                Auxiliary(pv.name, det.uid, registry, addRegistry=False)
            )
            if det.metadata is not None:
                json_meta = json.dumps(det.metadata)
                meta_group_aux.addSubAuxiliary(
                    Auxiliary(pv.name, json_meta, registry, addRegistry=False)
                )


def get_sensvol_metadata(registry: g4.Registry, name: str) -> object | None:
    """Load metadata attached to the given sensitive volume."""
    auxs = [aux for aux in registry.userInfo if aux.auxtype == "RMG_detector_meta"]
    if auxs == []:
        return None
    meta_aux = auxs[0]
    assert len(auxs) == 1

    meta_auxs = [aux for aux in meta_aux.subaux if aux.auxtype == name]
    if meta_auxs == []:
        return None
    assert len(meta_auxs) == 1
    return json.loads(meta_auxs[0].auxvalue)
