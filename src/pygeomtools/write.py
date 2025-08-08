from __future__ import annotations

import os

from pyg4ometry import gdml, geant4

from . import detectors, geometry, visualization


def write_pygeom(
    reg: geant4.Registry,
    gdml_file: str | os.PathLike | None = None,
    write_vis_auxvals: bool = True,
    *,
    ignore_duplicate_uids: bool | set[int] = False,
) -> None:
    """Commit all auxiliary data to the registry and write out a GDML file.

    Parameters
    ----------
    reg
        the pyg4ometry registry containing the geometry to be written.
    gdml_file
        GDML file to write, or ``None`` just for performing the other actions.
    write_vis_auxvals
        if ``False``, do not store colors in the output file.
    ignore_duplicate_uids
        skip the check for duplicate detector uids for all, or just some, uids.

    See also
    --------
    .detectors.write_detector_auxvals
    .detectors.check_detector_uniqueness
    .visualization.write_color_auxvals
    .geometry.check_registry_sanity
    """
    detectors.write_detector_auxvals(reg)
    if ignore_duplicate_uids is not True:
        detectors.check_detector_uniqueness(reg, ignore_duplicate_uids or set())
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
