from __future__ import annotations

import logging
from pathlib import Path

import pyg4ometry.geant4 as g4
from pyg4ometry.gdml.Defines import Auxiliary

log = logging.getLogger(__name__)


def _color_macro_recursive(lv: g4.LogicalVolume, macro_lines: dict) -> None:
    if hasattr(lv, "pygeom_color_rgba") and lv.name not in macro_lines:
        mac = f"/vis/geometry/set/forceSolid {lv.name}\n"
        if lv.pygeom_color_rgba is False or lv.pygeom_color_rgba[3] == 0:
            mac += f"/vis/geometry/set/visibility {lv.name} -1 false\n"
        else:
            rgba = " ".join([str(c) for c in lv.pygeom_color_rgba])
            mac += f"/vis/geometry/set/colour {lv.name} 0 {rgba}\n"
        macro_lines[lv.name] = mac

    for pv in lv.daughterVolumes:
        if pv.type == "placement":
            _color_macro_recursive(pv.logicalVolume, macro_lines)


def generate_color_macro(registry: g4.Registry, filename: str) -> None:
    """Create a Geant4 macro file containing the defined visualization attributes."""
    macro_lines = {registry.worldVolume: None}
    _color_macro_recursive(registry.worldVolume, macro_lines)
    macro_contents = "".join([m for m in macro_lines.values() if m is not None])

    with Path(filename).open("w", encoding="utf-8") as f:
        f.write(macro_contents)


def write_color_auxvals(registry: g4.Registry) -> None:
    """Append an auxiliary structure, storing the visualization color information."""
    written_lvs = set()

    def _append_color_recursive(lv: g4.LogicalVolume) -> None:
        if hasattr(lv, "pygeom_color_rgba") and lv.name not in written_lvs:
            if lv.pygeom_color_rgba is False or lv.pygeom_color_rgba[3] == 0:
                rgba = "-1"
            else:
                rgba = ",".join([str(c) for c in lv.pygeom_color_rgba])
            # remove existing colors.
            lv.auxiliary = [aux for aux in lv.auxiliary if aux.auxtype != "rmg_color"]
            lv.addAuxiliaryInfo(
                Auxiliary("rmg_color", rgba, registry, addRegistry=False)
            )
            written_lvs.add(lv.name)

        if hasattr(lv, "pygeom_colour_rgba"):
            msg = f"pygeom_colour_rgba on volume {lv.name} not supported, use use pygeom_color_rgba instead."
            raise RuntimeError(msg)

        for pv in lv.daughterVolumes:
            if pv.type == "placement":
                _append_color_recursive(pv.logicalVolume)

    written_lvs.add(registry.worldVolume.name)  # do not store world vis args.
    _append_color_recursive(registry.worldVolume)


def load_color_auxvals_recursive(lv: g4.LogicalVolume) -> None:
    auxvals = list(filter(lambda aux: aux.auxtype == "rmg_color", lv.auxiliary))
    if len(auxvals) > 1:
        log.warning("more than one rmg_color for LV %s", lv.name)
    # assert len(auxvals) <= 1

    if len(auxvals) > 0 and not hasattr(lv, "pygeom_color_rgba"):
        rgba = auxvals[-1].auxvalue
        if rgba == "-1":
            lv.pygeom_color_rgba = False
        else:
            lv.pygeom_color_rgba = list(map(float, rgba.split(",")))

    for pv in lv.daughterVolumes:
        if pv.type == "placement":
            load_color_auxvals_recursive(pv.logicalVolume)
