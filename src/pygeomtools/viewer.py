"""An opionionated wrapper around :class:`pyg4ometry.visualization.VtkViewerNew`."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pyg4ometry.geant4 as g4
import vtk
from pyg4ometry import config as meshconfig
from pyg4ometry import gdml
from pyg4ometry import visualisation as pyg4vis

from .utils import load_dict
from .visualization import load_color_auxvals_recursive

log = logging.getLogger(__name__)


def visualize(registry: g4.Registry, scenes: dict | None = None) -> None:
    if scenes is None:
        scenes = {}

    v = pyg4vis.VtkViewerColouredNew()
    v.addLogicalVolume(registry.worldVolume)

    load_color_auxvals_recursive(registry.worldVolume)
    registry.worldVolume.pygeom_color_rgba = False  # hide the wireframe of the world.
    _color_recursive(registry.worldVolume, v, scenes.get("color_overrides", {}))

    for clip in scenes.get("clipper", []):
        v.addClipper(clip["origin"], clip["normal"], bClipperCloseCuts=False)

    v.buildPipelinesAppend()
    v.addAxes(length=5000)
    v.axes[0].SetVisibility(False)  # hide axes by default.

    # override the interactor style.
    v.interactorStyle = _KeyboardInteractor(v.ren, v.iren, v, scenes)
    v.interactorStyle.SetDefaultRenderer(v.ren)
    v.iren.SetInteractorStyle(v.interactorStyle)

    # set some defaults
    if "default" in scenes:
        sc = scenes["default"]
        _set_camera(v, up=sc.get("up"), pos=sc.get("camera"), focus=sc.get("focus"))
    else:
        _set_camera(v, up=(1, 0, 0), pos=(0, 0, +20000))

    v.view()


class _KeyboardInteractor(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, renderer, iren, vtkviewer, scenes):
        self.AddObserver("KeyPressEvent", self.keypress)

        self.ren = renderer
        self.iren = iren
        self.vtkviewer = vtkviewer
        self.scenes = scenes

    def keypress(self, _obj, _event):
        # predefined: "e"xit

        key = self.iren.GetKeySym()
        if key == "a":  # toggle "a"xes
            ax = self.vtkviewer.axes[0]
            ax.SetVisibility(not ax.GetVisibility())

            self.ren.GetRenderWindow().Render()

        if key == "u":  # "u"p
            _set_camera(self, up=(0, 0, 1), pos=(-20000, 0, 0))

        if key == "t":  # "t"op
            _set_camera(self, up=(1, 0, 0), pos=(0, 0, +20000))

        sc_index = 1
        for sc in self.scenes.get("scenes", []):
            if key == f"F{sc_index}":
                _set_camera(
                    self, up=sc.get("up"), pos=sc.get("camera"), focus=sc.get("focus")
                )
                sc_index += 1

        if key == "s":  # "s"ave
            _export_png(self.vtkviewer)

        if key == "i":
            cam = self.ren.GetActiveCamera()
            print(f"- focus: {list(cam.GetFocalPoint())}")  # noqa: T201
            print(f"  up: {list(cam.GetViewUp())}")  # noqa: T201
            print(f"  camera: {list(cam.GetPosition())}")  # noqa: T201

        if key == "plus":
            _set_camera(self, dolly=1.1)
        if key == "minus":
            _set_camera(self, dolly=0.9)


def _set_camera(v, focus=None, up=None, pos=None, dolly=None) -> None:
    cam = v.ren.GetActiveCamera()
    if focus is not None:
        cam.SetFocalPoint(*focus)
    if up is not None:
        cam.SetViewUp(*up)
    if pos is not None:
        cam.SetPosition(*pos)
    if dolly is not None:
        cam.Dolly(dolly)

    v.ren.ResetCameraClippingRange()
    v.ren.GetRenderWindow().Render()


def _export_png(v, file_name="scene.png") -> None:
    ifil = vtk.vtkWindowToImageFilter()
    ifil.SetInput(v.renWin)
    ifil.ReadFrontBufferOff()
    ifil.Update()

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
    png.SetInputConnection(ifil.GetOutputPort())
    png.Write()


def _color_recursive(
    lv: g4.LogicalVolume, viewer: pyg4vis.ViewerBase, overrides: dict
) -> None:
    if hasattr(lv, "pygeom_color_rgba") or lv.name in overrides:
        color_rgba = overrides.get(lv.name, lv.pygeom_color_rgba)
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
            _color_recursive(pv.logicalVolume, viewer, overrides)


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
        "filename",
        help="""GDML file to visualize.""",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger("pygeomtools").setLevel(logging.DEBUG)
    if args.debug:
        logging.root.setLevel(logging.DEBUG)

    scene = {}
    if args.scene:
        scene = load_dict(args.scene)

    if scene.get("fine_mesh", args.fine):
        meshconfig.setGlobalMeshSliceAndStack(100)

    log.info("loading GDML geometry from %s", args.filename)
    registry = gdml.Reader(args.filename).getRegistry()

    log.info("visualizing...")
    visualize(registry, scene)
