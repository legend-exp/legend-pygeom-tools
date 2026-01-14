# `G4Region`s in GDML

The GDML parser of Geant4 supports reading regions from the GDML file from a
special auxiliary value structure. _pygeomtools_ provides a helper class to
create these GDML structures. A region groups logical volumes and can change
production cuts[^cuts_per_region] and user limits[^special_tracking_cuts].

In this example, we will define a region with a logical value that essentially
prevents all tracking by forcing a minimum track energy of 1 TeV. Combining this
with a sensitive detector, all particle energy will be recorded in one step.

```python
u = pint.get_application_registry()

region = pygeomtools.Region("my_region")
region.add_volume(volume_lv)

region.set_cuts(0.1 * u.mm)  # we _need_ to set defaults here.
region.uekinMin = 1000 * u.GeV
```

:::{tip} Region as overlay file

The region doesn't need to be defined in the same file as the geometry, but can
also be stored in an "overlay" file. The default writing functionality in
pyg4ometry/_legend-pygeom-tools_ expects a full geometry structure with a world
volume, which we cannot store in such an overlay file. To accommodate this use
case, the special writing function {func}`.write_pygeom_aux_only` has been
added:

```python
reg = g4.Registry()
region.add_to_gdml(reg)

pygeomtools.write_pygeom_aux_only(reg, "region-overlaygdml")
```

You can then use `remage -g geom.gdml region-overlay.gdml`.

:::

[^cuts_per_region]:
    https://geant4-userdoc.web.cern.ch/UsersGuides/ForApplicationDeveloper/html/TrackingAndPhysics/cutsPerRegion.html

[^special_tracking_cuts]:
    https://geant4-userdoc.web.cern.ch/UsersGuides/ForApplicationDeveloper/html/TrackingAndPhysics/thresholdVScut.html#special-tracking-cuts
