# GDML viewer

```text
usage: legend-pygeom-vis [-h] [--verbose] [--debug] [--fine] [--scene SCENE] [--add-points ADD_POINTS]
                         [--add-points-columns ADD_POINTS_COLUMNS]
                         filename

legend-pygeom-vis command line interface

positional arguments:
  filename              GDML file to visualize.

options:
  -h, --help            show this help message and exit
  --verbose, -v         Increase the program verbosity
  --debug, -d           Increase the program verbosity to maximum
  --fine                use finer meshing settings
  --scene SCENE, -s SCENE
                        scene definition file.
  --add-points ADD_POINTS
                        load points from LH5 file
  --add-points-columns ADD_POINTS_COLUMNS
                        columns in the point file stp/vertices:xloc,yloc,zloc

```

## Keyboard shortcuts

- `e` exit viewer
- `a` show/hide axes
- `u` side view
- `t` view from top
- `b` view from bottom
- `p` toggle parallel projection
- `s` save screenshot
- `i` dump current camera info (focal point, up vector, position)
- `v` toggle display of loaded points (see `--add-points`)
- `F<n>` switch to scene n
- `Home` switch to `default` scene
- `+` zoom in
- `-` zoom out

```{eval-rst}
.. _scene-file-format:
```

## scene file format

```yaml
# enable finer meshing for round surfaces
fine_mesh: true

# default position at startup of viewer
default:
  # focus point (units: mm)
  focus: [0, 0, 0]
  # up vector (dimensionless)
  up: [1, 0, 0]
  # camera position (units: mm)
  camera: [0, 0, 20000]
  # enable/disable parallel projection (optional, false or number)
  parallel: false

# clip through the geometry
clipper:
  - origin: [0, 0, 0]
    normal: [1, 0, 0]
    # close all clipped volumes (might give bad results, default is false).
    close_cuts: true

# other pre-defined scenes/camera positions
# can be opened by pressing F<n> (n is the 1-based index in this list)
# for details see the `default` config above.
scenes:
  - origin: [0, 0, 0]
    up: [0.55, 0, 0.82]
    pos: [-14000, 0, 8000]

  - # a scene with parallel projection
    origin: [0, 0, 0]
    up: [0.55, 0, 0.82]
    pos: [-14000, 0, 8000]
    # in parallel mode, the number here controls the zoom level.
    # the number is half the screen height in mm
    parallel: 2000

# override colors for logical volumes. Either a 4-tuple (RGBA, range 0-1) or false.
color_overrides:
  lar: false
  V02160A: [0, 1, 0, 1]
  # the keys are interpreted as regexes (they have to match the whole volume name).
  "fibers_.*": [0, 0, 1, 1]

# show points (e.g. vertices, hits) as overlay over the geometry from LH5 files.
# the units in the LH5 file will be respected.
points:
  - file: test-points.lh5
    table: stp/vertices
    columns: ["xloc", "yloc", "zloc"]
    color: [0, 1, 0, 1] # rgba tuple.
    size: 5 # marker size.

# add light and shadows.
light:
  pos: [5000, 5000, 2000]
  shadow: true
```
