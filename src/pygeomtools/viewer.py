"""An opionionated wrapper around :class:`pyg4ometry.visualization.VtkViewerNew`."""

from __future__ import annotations

import argparse
import copy
import logging
import re
from pathlib import Path

import numpy as np
import pyg4ometry.geant4 as g4
import vtk
from pyg4ometry import config as meshconfig
from pyg4ometry import gdml
from pyg4ometry import visualisation as pyg4vis

from .utils import load_dict
from .visualization import load_color_auxvals_recursive

log = logging.getLogger(__name__)


def visualize(registry: g4.Registry, scenes: dict | None = None, points=None) -> None:
    """Open a VTK-based viewer for the geometry and scene definition.

    Parameters
    ----------
    registry
        registry instance containing the geometry to view.
    scenes
        loaded :ref:`scene definition file <scene-file-format>`. note that the `fine_mesh`
        key is ignored and has to be set before loading/constructing the geometry.
    points
        show points, additionally to the points defined in the scene config.
    """
    if scenes is None:
        scenes = {}

    try:
        v = pyg4vis.VtkViewerColouredNew(defaultCutters=False)
    except TypeError:
        v = pyg4vis.VtkViewerColouredNew()
    v.addLogicalVolume(registry.worldVolume)

    v.pygeom_scenes = scenes

    load_color_auxvals_recursive(registry.worldVolume)
    registry.worldVolume.pygeom_color_rgba = False  # hide the wireframe of the world.
    _color_recursive(registry.worldVolume, v, scenes.get("color_overrides", {}))

    # add clippers.
    clippers = scenes.get("clipper", [])
    clippers_to_remove = []
    if len(clippers) > 1:
        msg = "only one clipper can be set at the same time."
        raise ValueError(msg)
    for clip in clippers:
        clippers_to_remove = clip.get("close_cuts_remove", [])
        v.addClipper(
            clip["origin"],
            clip["normal"],
            bClipperCloseCuts=clip.get("close_cuts", False),
        )

    v.buildPipelinesAppend()

    # implement partial clipping. this can be quite confusing, as this can only remove
    # based on shared VisOptions, and not by volume name. if a volume shares their
    # VisOptions with a volume in clippers_to_remove, the closing planes of both will
    # be removed.
    if len(clippers_to_remove) > 0:
        clip_remove_regex = f"({'|'.join(clippers_to_remove)})$"
        vo_to_remove_clip = {
            str(vo)
            for k, vol in v.instanceVisOptions.items()
            if re.match(clip_remove_regex, k)
            for vo in vol
        }
        for vo in vo_to_remove_clip:
            v.ren.RemoveActor(v.actors[f"{vo}_clipper"])

    v.addAxes(length=5000)
    v.axes[0].SetVisibility(False)  # hide axes by default.

    if points is not None:
        _add_points(v, points)

    for scene_points in scenes.get("points", []):
        points_array = _load_points(
            scene_points["file"],
            scene_points["table"],
            scene_points.get("columns", ["xloc", "yloc", "zloc"]),
            scene_points.get("n_rows", None),
        )
        _add_points(
            v,
            points_array,
            scene_points.get("color", (1, 1, 0, 1)),
            scene_points.get("size", 5),
        )

    # add light and shadow.
    if "light" in scenes:
        light = scenes["light"]
        _add_light_and_shadow(
            v, light_pos=light.get("pos"), shadow=light.get("shadow", True)
        )

    # override the interactor style.
    v.interactorStyle = _KeyboardInteractor(v.ren, v.iren, v, scenes)
    v.interactorStyle.SetDefaultRenderer(v.ren)
    v.iren.SetInteractorStyle(v.interactorStyle)

    # set some defaults
    _set_camera_scene(v, scenes.get("default"))

    v.view()


class _KeyboardInteractor(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, renderer, iren, vtkviewer, scenes):
        self.AddObserver("KeyPressEvent", self.keypress)

        self.ren = renderer
        self.iren = iren
        self.vtkviewer = vtkviewer
        self.scenes = scenes

    def keypress(self, _obj, _event):
        # predefined: _e_xit

        key = self.iren.GetKeySym()
        if key == "a":  # toggle _a_xes
            ax = self.vtkviewer.axes[0]
            ax.SetVisibility(not ax.GetVisibility())
            self.ren.GetRenderWindow().Render()

        if (
            key == "v"  # toggle _v_ertices
            and hasattr(self.vtkviewer, "points")
            and self.vtkviewer.points is not None
        ):
            pn = self.vtkviewer.points
            pn.SetVisibility(not ax.GetVisibility())
            self.ren.GetRenderWindow().Render()

        if key == "u":  # _u_p
            _set_camera(self.vtkviewer, up=(0, 0, 1), pos=(-20000, 0, 0))

        if key == "t":  # _t_op
            _set_camera(self.vtkviewer, up=(1, 0, 0), pos=(0, 0, +20000))

        if key == "b":  # _b_ottom
            _set_camera(self.vtkviewer, up=(-1, 0, 0), pos=(0, 0, -20000))

        if key == "p":  # _p_arralel projection
            cam = self.ren.GetActiveCamera()
            _set_camera(self.vtkviewer, parallel=not cam.GetParallelProjection())

        for sc_index, sc in enumerate(self.scenes.get("scenes", [])):
            if key == f"F{sc_index + 1}":
                _set_camera_scene(self.vtkviewer, sc)

        if key == "Home":
            _set_camera_scene(self.vtkviewer, self.scenes.get("default"))

        if key == "s":  # _s_ave
            _export_png(self.vtkviewer)

        if key == "i":  # dump camera _i_nfo
            cam = self.ren.GetActiveCamera()
            print(f"- focus: {list(cam.GetFocalPoint())}")  # noqa: T201
            print(f"  up: {list(cam.GetViewUp())}")  # noqa: T201
            print(f"  camera: {list(cam.GetPosition())}")  # noqa: T201
            if cam.GetParallelProjection():
                print(f"  parallel: {cam.GetParallelScale()}")  # noqa: T201

        if key == "plus":
            _set_camera(self.vtkviewer, dolly=1.1)
        if key == "minus":
            _set_camera(self.vtkviewer, dolly=0.9)


def _set_camera(
    v: pyg4vis.VtkViewerColouredNew,
    focus: tuple[float, float, float] | None = None,
    up: tuple[float, float, float] | None = None,
    pos: tuple[float, float, float] | None = None,
    dolly: float | None = None,
    parallel: bool | int | None = None,
) -> None:
    cam = v.ren.GetActiveCamera()
    if focus is not None:
        cam.SetFocalPoint(*focus)
    if up is not None:
        cam.SetViewUp(*up)
    if pos is not None:
        cam.SetPosition(*pos)
    if dolly is not None:
        if cam.GetParallelProjection():
            cam.SetParallelScale(1 / dolly * cam.GetParallelScale())
        else:
            cam.Dolly(dolly)
    if parallel is not None:
        cam.SetParallelProjection(int(parallel) > 0)
        if cam.GetParallelScale() == 1.0:
            # still at initial value, set to something more useful.
            cam.SetParallelScale(2000)
        if not isinstance(parallel, bool):
            cam.SetParallelScale(int(parallel))

    v.ren.ResetCameraClippingRange()
    v.ren.GetRenderWindow().Render()


def _set_camera_scene(v: pyg4vis.VtkViewerColouredNew, sc: dict) -> None:
    if sc is None:
        _set_camera(v, up=(1, 0, 0), pos=(0, 0, +20000))
    else:
        _set_camera(
            v,
            up=sc.get("up"),
            pos=sc.get("camera"),
            focus=sc.get("focus"),
            parallel=sc.get("parallel", False),
        )


def _export_png(v: pyg4vis.VtkViewerColouredNew, file_name: str = "scene.png") -> None:
    larger = vtk.vtkRenderLargeImage()
    larger.SetInput(v.ren)
    larger.SetMagnification(v.pygeom_scenes.get("export_scale", 1))

    # get a non-colliding file name.
    p = Path(file_name)
    stem = p.stem
    idx = 0
    while p.exists():
        p = p.with_stem(f"{stem}_{idx}")
        idx += 1
        if idx > 1000:
            msg = "could not find file name"
            raise ValueError(msg)

    png = vtk.vtkPNGWriter()
    png.SetFileName(str(p.absolute()))
    png.SetInputConnection(larger.GetOutputPort())
    png.Write()


def _add_points(v, points, color=(1, 1, 0, 1), size=5) -> None:
    # create vtkPolyData from points.
    vp = vtk.vtkPoints()
    ca = vtk.vtkCellArray()
    pd = vtk.vtkPolyData()

    for t in points:
        p = vp.InsertNextPoint(*t)
        ca.InsertNextCell(1)
        ca.InsertCellPoint(p)

    pd.SetPoints(vp)
    pd.SetVerts(ca)

    # add points to renderer.
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(pd)
    mapper.ScalarVisibilityOff()

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*color[0:3])
    actor.GetProperty().SetPointSize(size)
    actor.GetProperty().SetOpacity(color[3])
    actor.GetProperty().SetRenderPointsAsSpheres(True)

    v.ren.AddActor(actor)
    v.points = actor


def _load_points(
    lh5_file: str, point_table: str, columns: list[str], n_rows: int | None
):
    from lgdo import VectorOfVectors, lh5

    log.info(
        "loading table %s (with columns %s) from file %s",
        point_table,
        str(columns),
        lh5_file,
    )
    extra_kwargs = {}
    if n_rows is not None:
        extra_kwargs["n_rows"] = n_rows
    point_table = lh5.read(point_table, lh5_file, **extra_kwargs)

    # the points need to be in mm.
    cols = []
    for c in columns:
        col = point_table[c]
        if isinstance(col, VectorOfVectors):
            col = col.flattened_data.view_as("np", with_units=True)
        else:
            col = col.view_as("np", with_units=True)
        cols.append(col.to("mm").m)

    return np.array(cols).T


def _color_override_matches(overrides: dict, name: str):
    for pattern, color in overrides.items():
        if re.match(f"{pattern}$", name):
            return color
    return None


def _color_recursive(
    lv: g4.LogicalVolume, viewer: pyg4vis.ViewerBase, overrides: dict, level: int = 0
) -> None:
    if level == 0:
        # first, make sure that we have independent VisOption instances everywhere.
        default_vo = viewer.getDefaultVisOptions()
        for vol in viewer.instanceVisOptions:
            viewer.instanceVisOptions[vol] = [
                copy.copy(vo) if vo is default_vo else vo
                for vo in viewer.instanceVisOptions[vol]
            ]

    if hasattr(lv, "pygeom_colour_rgba"):
        log.warning(
            "pygeom_colour_rgba on volume %s not supported, use use pygeom_color_rgba instead.",
            lv.name,
        )

    color_override = _color_override_matches(overrides, lv.name)
    if hasattr(lv, "pygeom_color_rgba") or color_override is not None:
        color_rgba = lv.pygeom_color_rgba if hasattr(lv, "pygeom_color_rgba") else None
        color_rgba = color_override if color_override is not None else color_rgba
        assert color_rgba is not None

        for vis in viewer.instanceVisOptions[lv.name]:
            if color_rgba is False:
                vis.alpha = 0
                vis.visible = False
            else:
                vis.colour = color_rgba[0:3]
                vis.alpha = color_rgba[3]
                vis.visible = vis.alpha > 0

    for pv in lv.daughterVolumes:
        if pv.type == "placement":
            _color_recursive(pv.logicalVolume, viewer, overrides, level + 1)


def _add_light_and_shadow(
    v: pyg4vis.VtkViewerColouredNew,
    light_pos: tuple[float, float, float],
    shadow: bool,
) -> None:
    lc = vtk.vtkNamedColors()
    lc.SetColor("LightColor", [255, 255, 251, 255])
    light = vtk.vtkLight()
    light.SetFocalPoint(0, 0, 0)
    light.SetPosition(*light_pos)
    light.SetIntensity(1)
    light.SetColor(lc.GetColor3d("LightColor"))
    v.ren.AddLight(light)

    if shadow:
        passes = vtk.vtkRenderPassCollection()
        shadows = vtk.vtkShadowMapPass()
        passes.AddItem(shadows.GetShadowMapBakerPass())
        passes.AddItem(shadows)
        passes.AddItem(vtk.vtkDefaultPass())
        seq = vtk.vtkSequencePass()
        seq.SetPasses(passes)

        camera_pass = vtk.vtkCameraPass()
        camera_pass.SetDelegatePass(seq)
        v.ren.SetPass(camera_pass)


def vis_gdml_cli() -> None:
    parser = argparse.ArgumentParser(
        prog="legend-pygeom-vis",
        description="%(prog)s command line interface",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="""Increase the program verbosity""",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="""Increase the program verbosity to maximum""",
    )
    parser.add_argument(
        "--fine",
        action="store_true",
        help="""use finer meshing settings""",
    )
    parser.add_argument(
        "--scene",
        "-s",
        help="""scene definition file.""",
    )
    parser.add_argument(
        "--add-points",
        help="""load points from LH5 file""",
    )
    parser.add_argument(
        "--add-points-columns",
        default="vtx:xloc,yloc,zloc",
        help="""columns in the point file %(default)s""",
    )

    parser.add_argument(
        "filename",
        help="""GDML file to visualize.""",
    )

    args = parser.parse_args()

    logging.basicConfig()
    if args.verbose:
        logging.getLogger("pygeomtools").setLevel(logging.DEBUG)
    if args.debug:
        logging.root.setLevel(logging.DEBUG)

    scene = {}
    if args.scene:
        scene = load_dict(args.scene)

    if scene.get("fine_mesh", args.fine):
        meshconfig.setGlobalMeshSliceAndStack(100)

    points = None
    if args.add_points:
        table_parts = [c.strip() for c in args.add_points_columns.split(":")]
        point_table = table_parts[0]
        point_columns = [c.strip() for c in table_parts[1].split(",")]
        if len(table_parts) != 2 or len(point_columns) != 3:
            msg = "invalid parameter for points"
            raise ValueError(msg)

        points = _load_points(args.add_points, point_table, point_columns, None)

    log.info("loading GDML geometry from %s", args.filename)
    registry = gdml.Reader(args.filename).getRegistry()

    log.info("visualizing...")
    visualize(registry, scene, points)
