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
- `s` save screenshot
- `i` dump current camera info (focal point, up vector, position)
- `p` toggle display of loaded points (see `--add-points`)
- `F<n>` switch to scene n
- `+` zoom in
- `-` zoom out

## scene file format

```yaml
# enable finer meshing for round surfaces
fine_mesh: true

# default position at startup of viewer
default:
  # focal point
  focus: [0, 0, 0]
  # up-vector
  up: [1, 0, 0]
  # camera position
  camera: [0, 0, 20000]

# clip through the geometry
clipper:
  - origin: [0, 0, 0]
    normal: [1, 0, 0]

# other pre-defined scenes
# can be opened by pressing F<n> (n is the 1-based index in this list)
scenes:
  - origin: [0, 0, 0]
    up: [0.55, 0, 0.82]
    pos: [-14000, 0, 8000]

# override colors of specified logical volumes
color_overrides:
  lar: False
```
