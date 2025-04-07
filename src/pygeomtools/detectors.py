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

AUXKEY_DETMETA = "RMG_detector_meta"
AUXKEY_DET = "RMG_detector"


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
    """Iterate over all physical volumes that have a :class:`RemageDetectorInfo` attached.

    Important
    ---------
    this only returns instances previously set via
    :meth:`get_pygeom_active_detector() <pyg4ometry.geant4.PhysicalVolume.get_pygeom_active_detector>`,
    not data loaded from GDML. Use :meth:`get_all_sensvols` instead for that use case.
    """

    if isinstance(pv, g4.PhysicalVolume):
        det = pv.get_pygeom_active_detector()
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
    if _get_rmg_detector_aux(registry, raise_on_missing=False) is not None:
        sensvols = get_all_sensvols(registry)
    else:
        sensvols = {pv.name: det for pv, det in walk_detectors(registry)}

    macro_lines = {}
    for pv, det in sensvols.items():
        if pv in macro_lines:
            continue
        mac = f"/RMG/Geometry/RegisterDetector {det.detector_type.title()} {pv} {det.uid}\n"
        macro_lines[pv] = mac

    macro_contents = "".join(macro_lines.values())

    with Path(filename).open("w", encoding="utf-8") as f:
        f.write(macro_contents)


def write_detector_auxvals(registry: g4.Registry) -> None:
    """Append an auxiliary structure, storing the sensitive detector volume information.

    .. note::
        see :doc:`../metadata` for a reference of the written structure.
    """
    if _get_rmg_detector_aux(registry, raise_on_missing=False) is not None:
        msg = "detector auxiliary structure already written"
        raise RuntimeError(msg)

    written_pvs = set()
    group_it = groupby(
        sorted(walk_detectors(registry), key=lambda d: d[1].detector_type),
        lambda d: d[1].detector_type,
    )

    meta_group_aux = Auxiliary(AUXKEY_DETMETA, "", registry)

    for key, group in group_it:
        group_aux = Auxiliary(AUXKEY_DET, key, registry)

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


def _get_rmg_detector_aux(
    registry: g4.Registry, *, raise_on_missing: bool = True
) -> Auxiliary | None:
    auxs = [aux for aux in registry.userInfo if aux.auxtype == AUXKEY_DETMETA]
    if auxs == []:
        if not raise_on_missing:
            return None
        msg = f"GDML missing {AUXKEY_DETMETA} auxval (not written by legend-pygeom-tools?)"
        raise RuntimeError(msg)
    assert len(auxs) == 1
    return auxs[0]


def get_sensvol_metadata(registry: g4.Registry, name: str) -> AttrsDict | None:
    """Load metadata attached to the given sensitive volume (from GDML)."""
    meta_aux = _get_rmg_detector_aux(registry)
    meta_auxs = [aux for aux in meta_aux.subaux if aux.auxtype == name]
    if meta_auxs == []:
        return None
    assert len(meta_auxs) == 1
    return AttrsDict(json.loads(meta_auxs[0].auxvalue))


def get_all_sensvols(registry: g4.Registry) -> dict[str, RemageDetectorInfo]:
    """Load all registered sensitive detectors with their metadata (from GDML)."""
    meta_aux = _get_rmg_detector_aux(registry)
    meta_auxs = {
        aux.auxtype: AttrsDict(json.loads(aux.auxvalue)) for aux in meta_aux.subaux
    }

    detmapping = {}
    type_auxs = [aux for aux in registry.userInfo if aux.auxtype == AUXKEY_DET]
    for type_aux in type_auxs:
        for det_aux in type_aux.subaux:
            detmapping[det_aux.auxtype] = RemageDetectorInfo(
                type_aux.auxvalue, int(det_aux.auxvalue), meta_auxs.get(det_aux.auxtype)
            )

    if set(meta_auxs.keys()) - set(detmapping.keys()) != set():
        msg = "invalid GDML auxval structure (meta keys and detmapping keys differ)"
        raise RuntimeError(msg)

    return detmapping


def get_sensvol_by_uid(
    registry: g4.Registry, uid: int
) -> tuple[str, RemageDetectorInfo] | None:
    """Get the volume name and detector metadata for the detector with remage detector ID `uid`."""
    sensvols = get_all_sensvols(registry)
    found = next(filter(lambda s: s[1].uid == uid, sensvols.items()), None)
    if found is None:
        return None
    return found


def __set_pygeom_active_detector(self, det_info: RemageDetectorInfo | None) -> None:
    """Set the remage detector info on this physical volume instance."""
    if not isinstance(self, g4.PhysicalVolume):
        msg = "patched-in function called on wrong type"
        raise TypeError(msg)
    assert self.registry is not None
    if _get_rmg_detector_aux(self.registry, raise_on_missing=False) is not None:
        msg = "detector auxiliary structure already written"
        raise RuntimeError(msg)
    self.__pygeom_active_detector = det_info


def __get_pygeom_active_detector(self) -> RemageDetectorInfo | None:
    """Get the remage detector info on this physical volume instance."""
    if not isinstance(self, g4.PhysicalVolume):
        msg = "patched-in function called on wrong type"
        raise TypeError(msg)

    if hasattr(self, "__pygeom_active_detector"):
        return self.__pygeom_active_detector
    return None


def __patch_pyg4_pv():
    """monkey-patch a new function onto every PhysicalVolume instance."""
    t = g4.PhysicalVolume
    t.set_pygeom_active_detector = __set_pygeom_active_detector
    t.get_pygeom_active_detector = __get_pygeom_active_detector

    prop = property(__get_pygeom_active_detector)
    t.pygeom_active_detector = prop.setter(__set_pygeom_active_detector)

    def _wrap_warn(fn):
        def _fn(*args):
            import warnings

            warnings.warn(
                "pygeom_active_dector (typo!) is deprecated, use pygeom_active_detector instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            return fn(*args)

        return _fn

    prop = property(_wrap_warn(__get_pygeom_active_detector))
    t.pygeom_active_dector = prop.setter(_wrap_warn(__set_pygeom_active_detector))


__patch_pyg4_pv()
