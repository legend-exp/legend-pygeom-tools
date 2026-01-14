from __future__ import annotations

import pint
from pyg4ometry import geant4 as g4


def test_region(tmp_path):
    from pygeomtools import Region, write_pygeom_aux_only

    u = pint.get_application_registry()

    region = Region("my_region")
    region.add_volume("volume")

    region.set_cuts(0.1 * u.mm)  # we _need_ to set defaults here.
    region.uekinMin = 1000 * u.GeV

    reg = g4.Registry()
    region.add_to_gdml(reg)

    write_pygeom_aux_only(reg, tmp_path / "test_region.gdml")
