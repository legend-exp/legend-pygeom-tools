from __future__ import annotations

from collections.abc import Sequence

import pint
import pyg4ometry.geant4 as g4
from pyg4ometry.gdml.Defines import Auxiliary
from pygeomoptics.pyg4utils import pint_to_gdml

u = pint.get_application_registry()


class Region:
    """Store the definition of a G4Region in a GDML registry.

    .. important::
        All of the values ecut/poscut/pcut/gamcut must be explicitly set, otherwise
        Geant4 would assume a production cut of 0 mm, which is probably undesired.
    """

    name: str
    """name of this Geant4 region."""
    volumes: Sequence[str]
    """volumes to add this region to."""

    pcut: pint.Quantity | None = None
    """Production cut (length) for protons."""
    ecut: pint.Quantity | None = None
    """Production cut (length) for electrons."""
    poscut: pint.Quantity | None = None
    """Production cut (length) for positrons."""
    gamcut: pint.Quantity | None = None
    """Production cut (length) for gammas."""

    ustepMax: pint.Quantity | None = None
    """Maximum step length."""
    utrakMax: pint.Quantity | None = None
    """Maximum total track length."""
    utimeMax: pint.Quantity | None = None
    """Maximum global time for a track."""
    uekinMin: pint.Quantity | None = None
    """Minimum remaining kinetic energy for a track."""
    urangMin: pint.Quantity | None = None
    """Minimum remaining range for a track."""

    def __init__(self, name: str):
        self.name = name
        self.volumes = []

    def set_cuts(self, default: pint.Quantity = 0.1 * u.mm) -> None:
        """Set all production cuts to the specified length."""
        cut_fields = ("pcut", "ecut", "poscut", "gamcut")
        for cut in cut_fields:
            setattr(self, cut, default)

    def add_volume(self, vol: str | g4.LogicalVolume) -> None:
        self.volumes.append(vol if isinstance(vol, str) else vol.name)

    def add_to_gdml(self, registry: g4.Registry) -> Auxiliary:
        auxs = []
        for vol in self.volumes:
            auxs.append(Auxiliary("volume", vol, registry, addRegistry=False))

        # cuts are non-optional, as they default to 0...
        cut_fields = ("pcut", "ecut", "poscut", "gamcut")
        for cut in cut_fields:
            cutval = getattr(self, cut)
            if cutval is None or not cutval.check("[length]") or cutval.m < 0:
                msg = f"cut {cut} must be set and a positive length value"
                raise ValueError(msg)
            cutval_u, cutval_m = pint_to_gdml(cutval)
            auxs.append(
                Auxiliary(
                    cut, str(cutval_m), registry, unit=cutval_u, addRegistry=False
                )
            )

        ulim_auxs = []
        ulim_fields = {
            "ustepMax": "[length]",
            "utrakMax": "[length]",
            "utimeMax": "[time]",
            "uekinMin": "[energy]",
            "urangMin": "[length]",
        }
        for ulim, ulunitcat in ulim_fields.items():
            ulval = getattr(self, ulim)
            if ulval is None or not ulval.check(ulunitcat):
                continue
            ulval_u, ulval_m = pint_to_gdml(ulval)
            ulim_auxs.append(
                Auxiliary(ulim, str(ulval_m), registry, unit=ulval_u, addRegistry=False)
            )

        # ulims are optional, they are read with sane defaults.
        if ulim_auxs != []:
            ulim_aux = Auxiliary("ulimits", "", registry, addRegistry=False)
            for subaux in ulim_auxs:
                ulim_aux.addSubAuxiliary(subaux)
            auxs.append(ulim_aux)

        aux = Auxiliary("Region", self.name, registry, addRegistry=True)
        for subaux in auxs:
            aux.addSubAuxiliary(subaux)
        return aux
