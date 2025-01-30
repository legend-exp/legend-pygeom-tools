from __future__ import annotations

import os

from pyg4ometry import gdml, geant4

from . import detectors, geometry, visualization


def write_pygeom(
    reg: geant4.Registry,
    gdml_file: str | os.PathLike | None = None,
    write_vis_auxvals: bool = True,
) -> None:
    """Commit all auxiliary data to the registry and write out a GDML file."""
    detectors.write_detector_auxvals(reg)
    if write_vis_auxvals:
        visualization.write_color_auxvals(reg)
    geometry.check_registry_sanity(reg, reg)

    if gdml_file is not None:
        # pyg4ometry has added color writing in their bdsim style by default in 2025.
        try:
            w = gdml.Writer(writeColour=False)
        except TypeError:
            w = gdml.Writer()

        w.addDetector(reg)
        w.write(str(gdml_file))
