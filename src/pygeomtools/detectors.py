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
from dbetto import AttrsDict
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

    if isinstance(pv, g4.PhysicalVolume):
        det = None
        if hasattr(pv, "pygeom_active_detector"):
            det = pv.pygeom_active_detector
        elif hasattr(pv, "pygeom_active_dector"):
            import warnings

            warnings.warn(
                "pygeom_active_dector (typo!) is deprecated, use pygeom_active_detector instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            det = pv.pygeom_active_dector
        if det is not None:
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
            continue
        mac = f"/RMG/Geometry/RegisterDetector {det.detector_type.title()} {pv.name} {det.uid}\n"
        macro_lines[pv.name] = mac

    macro_contents = "".join(macro_lines.values())

    with Path(filename).open("w", encoding="utf-8") as f:
        f.write(macro_contents)


def write_detector_auxvals(registry: g4.Registry) -> None:
    """Append an auxiliary structure, storing the sensitive detector volume information.

    .. note::
        see <metadata> for a reference
    """
    written_pvs = set()
    group_it = groupby(walk_detectors(registry), lambda d: d[1].detector_type)

    meta_group_aux = Auxiliary("RMG_detector_meta", "", registry)

    for key, group in group_it:
        group_aux = Auxiliary("RMG_detector", key, registry)

        for pv, det in group:
            if pv.name in written_pvs:
                continue
            written_pvs.add(pv.name)

            group_aux.addSubAuxiliary(
                Auxiliary(pv.name, det.uid, registry, addRegistry=False)
            )
            if det.metadata is not None:
                json_meta = json.dumps(det.metadata)
                meta_group_aux.addSubAuxiliary(
                    Auxiliary(pv.name, json_meta, registry, addRegistry=False)
                )


def get_sensvol_metadata(registry: g4.Registry, name: str) -> AttrsDict | None:
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
    return AttrsDict(json.loads(meta_auxs[0].auxvalue))


def get_all_sensvols(registry: g4.Registry) -> dict[str, RemageDetectorInfo]:
    """Load all registered sensitive detectors with their metadata."""
    auxs = [aux for aux in registry.userInfo if aux.auxtype == "RMG_detector_meta"]
    if auxs == []:
        meta_auxs = {}
    else:
        assert len(auxs) == 1
        meta_auxs = {
            aux.auxtype: AttrsDict(json.loads(aux.auxvalue)) for aux in auxs[0].subaux
        }

    detmapping = {}
    type_auxs = [aux for aux in registry.userInfo if aux.auxtype == "RMG_detector"]
    for type_aux in type_auxs:
        for det_aux in type_aux.subaux:
            detmapping[det_aux.auxtype] = RemageDetectorInfo(
                type_aux.auxvalue, int(det_aux.auxvalue), meta_auxs.get(det_aux.auxtype)
            )

    if set(meta_auxs.keys()) - set(detmapping.keys()) != set():
        msg = "invalid GDML auxval structure"
        raise RuntimeError(msg)

    return detmapping


def __set_pygeom_active_detector(self, det_info: RemageDetectorInfo | None) -> None:
    """Set the remage detector info on this physical volume instance."""
    if not isinstance(self, g4.PhysicalVolume):
        msg = "patched-in function called on wrong type"
        raise TypeError(msg)
    self.pygeom_active_detector = det_info


def __get_pygeom_active_detector(self) -> RemageDetectorInfo | None:
    """Get the remage detector info on this physical volume instance."""
    if not isinstance(self, g4.PhysicalVolume):
        msg = "patched-in function called on wrong type"
        raise TypeError(msg)
    if hasattr(self, "pygeom_active_detector"):
        return self.pygeom_active_detector
    return None


# monkey-patch a new function onto every PhysicalVolume instance:
g4.PhysicalVolume.set_pygeom_active_detector = __set_pygeom_active_detector
g4.PhysicalVolume.get_pygeom_active_detector = __get_pygeom_active_detector
