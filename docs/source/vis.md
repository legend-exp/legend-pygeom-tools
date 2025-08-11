(gdml-viewer)=

# GDML viewer

The standalone GDML viewer application _legend-pygeom-vis_ is a CLI wrapper
around {func}`pygeomtools.viewer.visualize`. It can be used to view any GDML
file that can be read by pyg4ometry; the full set of features (coloring, ...) is
only available with files written with _legend-pygeom-tools_.

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
                        columns in the point file. default: vtx:xloc,yloc,zloc

```

## Keyboard shortcuts

The GUI viewer supports some keyboard shortcuts:

- `e` exit viewer
- `a` show/hide x/y/z axes
- `u` [_pre-defined scene_] side view
- `t` [_pre-defined scene_] view from top
- `b` [_pre-defined scene_] view from bottom
- `p` toggle parallel projection
- `s` save screenshot. The files are named `scene.png` by default, an
  incremented index will be added to the file name to avoid overwriting extsing
  images.
- `i` dump current camera info (focal point, up vector, position); in a format
  suitable for use in a scene file.
- `v` toggle display of loaded points (see `--add-points` and the section below)
- `F<n>` switch to scene n, as defined in the scene file
- `Home` switch to `default` scene
- `+` zoom in
- `-` zoom out

(scene-file)=

## scene file format

The viewer provided by this package (both the CLI tool and
{func}`pygeomtools.viewer.visualize`) can be configured by an extensive scene
file. This file can change the appearance of the rendered geometry model in
various ways.

The basic options are shown in an annotated example file:

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
```

### for visualization of (simulated) data

The viewer supports showing points (e.g. vertices, hits) as overlay over the
geometry from LH5 files. The units in the LH5 file will be respected and will be
scaled to show correctly over the geometry. Both the flat and the jagged remage
output options are supported for this feature.

```yaml
# show points as overlay over the geometry from LH5 files.
points:
  - file: test-points.lh5
    table: vtx
    columns: ["xloc", "yloc", "zloc"]
    n_rows: null # = all rows, or a number as a limit.
    color: [0, 1, 0, 1] # rgba tuple.
    size: 5 # marker size.
```

with `evtid: 1234` the viewer also supports a crude way of visualizing a single
event.

### advanced rendering and export options

:::{note}

These features are usually only required for creating high-quality renderings of
geometries.

:::

```yaml
# add a light source and shadows to produce a more realistically looking rendering.
light:
  pos: [5000, 5000, 2000] # units: mm
  shadow: true

# with this setting, the exported PNG files can be larger than the rendering window on
# screen. This has to be an integer.
export_scale: 1
# set the size of the window and the (unscaled) image. With export_scale set, the
# exported images will have a size equals to export_scale * window_size
window_size: [300, 400] # units: px
# directly export the image of the default view to this file name and exit the viewer.
export_and_exit: "filename_to_export.png"

# as mentioned above, the clipper might produce unexpected shapes when closing the cuts,
# however, closing cuts is necessary fdor well-looking renderings. close_cuts_remove
# provides a manual way to avoid the named volumes (regexes are supported) from being
# closed by the clipper.
clipper:
  - other_properties: ...
    close_cuts_remove: ["lar", "wlsr_ttx", "minishroud_.*", "fiber_.*"]
```
