# Welcome to legendtools's documentation!

This package provides shared code for the pyg4ometry-based Monte Carlo
geometries for the LEGEND-200 and LEGEND-1000 experiments.

## For geometry writers

If your geometry creation script/notebook/application is already set up
correctly, you can use our {doc}`extensions to the pyg4ometry API <pyg4-api>` to
control the package's output.

Detector registration and visualization attributes will be stored into the
output GDML file.

(detector-registration)=

### Registering detectors for use with [_remage_](https://github.com/legend-exp/remage)

On a physical volume instance, you can attach a
{attr}`pygeom_active_detector <pyg4ometry.geant4.PhysicalVolume.pygeom_active_detector>`,
e.g.

```python
from pygeomtools import RemageDetectorInfo

pv = g4.PhysicalVolume(...)

# attach an active detector to this physical volume.
pv.set_pygeom_active_detector(
    RemageDetectorInfo(
        "optical",  # detector type. The available options are defined by remage.
        1,  # detector id in remage.
        {"some": "metadata"},  # user-defined data (optional) that is stored into GDML.
    )
)
```

### Adjusting the visualization

On a logical volume instance, you can set
{attr}`pygeom_color_rgba <pyg4ometry.geant4.LogicalVolume.pygeom_color_rgba>`,
e.g.

```python
lv = g4.LogicalVolume(...)

# hide this volume in the visualization
lv.pygeom_color_rgba = False

# set the vis coloring to the given RGBA value. All 4 numbers should be given in the range 0–1.
lv.pygeom_color_rgba = (r, g, b, a)
```

## For application developers (general setup)

The added information will _not_ be written out directly when using only
pyg4ometry's writing functionality. However, _legend-pygeom-tools_ provides the
single function {func}`pygeomtools.write.write_pygeom` that combines committing
the extra information to the auxiliary data stores and writing everything to the
output file:

```python
from pygeomtools import detectors, geometry, visualization, write_pygeom

reg = geant4.Registry()

# your geometry building
# include some of the things described above (detectors, coloring)
# ...

# commit all auxiliary data to the registry and write out the GDML file. Use None as
# file name to suppress writing a file (e.g. when you only want to visualize)
write_pygeom(reg, "test.gdml")
```

## For geometry reading applications

_legend-pygeom-tools_ also provides functionality for applications that need to
load geometry files. These operate on a registry loaded via
{class}`pyg4ometry.gdml.Reader` from a file previously created with
_legend-pygeom-tools_. These functions can be used to get the mapping of volumes
to detector uid, and can also get the attached metadata snippets:

- {func}`pygeomtools.detectors.get_all_sensvols`
- {func}`pygeomtools.detectors.get_sensvol_by_uid`
- {func}`pygeomtools.detectors.get_sensvol_metadata`

## Table of Contents

```{toctree}
:maxdepth: 1

Metadata in GDML <metadata>
GDML viewer <vis>
Package API reference <api/modules>
pyg4ometry API extensions <pyg4-api>
```
