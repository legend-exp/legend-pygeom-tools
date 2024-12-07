"""An opionionated wrapper around :class:`pyg4ometry.visualization.VtkViewerNew`.

=================  ===============
Keyboard shortcut  Description
=================  ===============
``e``              exit viewer
``a``              show/hide axes
``u``              side view
``t``              view from top
``s``              save screenshot
``+``              zoom in
``-``              zoom out
=================  ===============
"""

from __future__ import annotations

import argparse
import logging

import pyg4ometry.geant4 as g4
import vtk
from pyg4ometry import config as meshconfig
from pyg4ometry import gdml
from pyg4ometry import visualisation as pyg4vis

from .visualization import load_color_auxvals_recursive

log = logging.getLogger(__name__)


def visualize(registry: g4.Registry) -> None:
    v = pyg4vis.VtkViewerColouredNew()
    v.addLogicalVolume(registry.worldVolume)

    load_color_auxvals_recursive(registry.worldVolume)
    registry.worldVolume.pygeom_color_rgba = False  # hide the wireframe of the world.
    _color_recursive(registry.worldVolume, v)

    # v.addClipper([0, 0, 0], [1, 0, 0], bClipperCloseCuts=False)

    v.buildPipelinesAppend()
    v.addAxes(length=5000)
    v.axes[0].SetVisibility(False)  # hide axes by default.

    # override the interactor style.
    v.interactorStyle = _KeyboardInteractor(v.ren, v.iren, v)
    v.interactorStyle.SetDefaultRenderer(v.ren)
    v.iren.SetInteractorStyle(v.interactorStyle)

    # set some defaults
    _set_camera(v, up=(1, 0, 0), pos=(0, 0, +20000))

    v.view()


class _KeyboardInteractor(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, renderer, iren, vtkviewer):
        self.AddObserver("KeyPressEvent", self.keypress)

        self.ren = renderer
        self.iren = iren
        self.vtkviewer = vtkviewer

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

        if key == "F1":
            _set_camera(self, up=(0.55, 0, 0.82), pos=(-14000, 0, 8000))

        if key == "s":  # "s"ave
            _export_png(self.vtkviewer)

        if key == "plus":
            _set_camera(self, dolly=1.1)
        if key == "minus":
            _set_camera(self, dolly=0.9)


def _set_camera(v, up=None, pos=None, dolly=None):
    cam = v.ren.GetActiveCamera()
    if up is not None:
        cam.SetViewUp(*up)
    if pos is not None:
        cam.SetPosition(*pos)
    if dolly is not None:
        cam.Dolly(dolly)

    v.ren.ResetCameraClippingRange()
    v.ren.GetRenderWindow().Render()


def _export_png(v, fileName="scene.png"):
    ifil = vtk.vtkWindowToImageFilter()
    ifil.SetInput(v.renWin)
    ifil.ReadFrontBufferOff()
    ifil.Update()

    png = vtk.vtkPNGWriter()
    png.SetFileName("./" + fileName)
    png.SetInputConnection(ifil.GetOutputPort())
    png.Write()


def _color_recursive(lv: g4.LogicalVolume, viewer: pyg4vis.ViewerBase) -> None:
    if hasattr(lv, "pygeom_color_rgba"):
        for vis in viewer.instanceVisOptions[lv.name]:
            if lv.pygeom_color_rgba is False:
                vis.alpha = 0
                vis.visible = False
            else:
                vis.colour = lv.pygeom_color_rgba[0:3]
                vis.alpha = lv.pygeom_color_rgba[3]
                vis.visible = vis.alpha > 0

    for pv in lv.daughterVolumes:
        if pv.type == "placement":
            _color_recursive(pv.logicalVolume, viewer)


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
        "filename",
        help="""GDML file to visualize.""",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger("pygeomtools").setLevel(logging.DEBUG)
    if args.debug:
        logging.root.setLevel(logging.DEBUG)

    if args.fine:
        meshconfig.setGlobalMeshSliceAndStack(100)

    msg = f"loading GDML geometry from {args.filename}"
    log.info(msg)
    registry = gdml.Reader(args.filename).getRegistry()

    log.info("visualizing...")
    visualize(registry)
