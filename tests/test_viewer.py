from __future__ import annotations

import json
from pathlib import Path

import lh5
import pytest
import vtk
from lgdo import Array, Table, VectorOfVectors
from pyg4ometry import gdml

from pygeomtools import viewer


def _offscreen_gl_available() -> bool:
    """Return True if the VTK build can render offscreen (EGL or OSMesa)."""
    try:
        vtk.vtkGraphicsFactory().SetOffScreenOnlyMode(1)
        ren_win = vtk.vtkRenderWindow()
        ren_win.SetOffScreenRendering(1)
        ren_win.AddRenderer(vtk.vtkRenderer())
        ren_win.SetSize(16, 16)
        ren_win.Render()
        ok = bool(ren_win.GetOffScreenRendering())
        ren_win.Finalize()
        return ok
    except Exception:
        return False


@pytest.fixture
def points_file(tmp_path):
    file = tmp_path / "points.lh5"

    data = {}
    data["evtid"] = Array([0, 1])

    attrs = {"units": "m"}
    data["xloc"] = VectorOfVectors([[0.1, 0.2], [-0.3, 0.4, -0.5]], attrs=attrs)
    data["yloc"] = VectorOfVectors([[0.1, 0.2], [-0.3, 0.4, -0.5]], attrs=attrs)
    data["zloc"] = VectorOfVectors([[0.1, 0.2], [-0.3, 0.4, -0.5]], attrs=attrs)

    tab = Table(data)
    lh5.write(tab, "stp/test", file, wo_mode="of")

    return str(file)


@pytest.mark.skipif(
    not _offscreen_gl_available(),
    reason="no offscreen GL backend (EGL/OSMesa) available",
)
def test_viewer_headless_export(tmp_path):
    """Smoke test for the headless PNG export path on EGL-only VTK builds."""
    registry = gdml.Reader(Path(__file__).parent / "geometry.gdml").getRegistry()

    output_file = tmp_path / "headless.png"
    output_file.unlink(missing_ok=True)

    viewer.visualize(
        registry,
        {
            "window_size": [200, 300],
            "export_and_exit": output_file,
            "default": {
                "up": [0, 0, 1],
                "camera": [-2000, 2000, 2000],
                "focus": [0, 0, 0],
                "parallel": False,
            },
        },
    )

    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_viewer(tmp_path, points_file):
    registry = gdml.Reader(Path(__file__).parent / "geometry.gdml").getRegistry()

    output_file = tmp_path / "test_viewer.png"
    output_file.unlink(missing_ok=True)

    vis_scene = {
        "window_size": [400, 700],
        "color_overrides": {
            "World": [1, 0, 0, 0.1],
        },
        "light": {
            "pos": [100, 100, 100],
            "shadow": True,
        },
        "export_scale": 2,
        "export_and_exit": output_file,
    }
    viewer.visualize(registry, vis_scene)

    # test adding a clipper.
    output_file = tmp_path / "test_viewer_clipper.png"
    output_file.unlink(missing_ok=True)

    vis_scene["clipper"] = [
        {"origin": [0, 0, 0], "normal": [0, 1, 0], "close_cuts": True}
    ]
    vis_scene["export_and_exit"] = output_file
    viewer.visualize(registry, vis_scene)

    # test showing points.
    output_file = tmp_path / "test_viewer_points.png"
    output_file.unlink(missing_ok=True)

    vis_scene["points"] = [
        {"file": points_file, "table": "stp/test", "size": 20, "color": [1, 0, 0, 1]}
    ]
    vis_scene["export_and_exit"] = output_file
    viewer.visualize(registry, vis_scene)


def test_viewer_cli(tmp_path, points_file):
    geom = Path(__file__).parent / "geometry.gdml"

    output_file = tmp_path / "test_viewer_cli.png"
    output_file.unlink(missing_ok=True)

    tmp_scene = tmp_path / "scene.yml"
    vis_scene = {
        "window_size": [400, 700],
        "export_scale": 2,
        "export_and_exit": str(output_file),
    }
    tmp_scene.write_text(json.dumps(vis_scene))

    viewer.vis_gdml_cli(["--scene", str(tmp_scene), str(geom)])

    # test showing points.
    output_file = tmp_path / "test_viewer_cli_points.png"
    output_file.unlink(missing_ok=True)

    vis_scene["export_and_exit"] = str(output_file)
    tmp_scene.write_text(json.dumps(vis_scene))
    viewer.vis_gdml_cli(
        [
            "--scene",
            str(tmp_scene),
            "--add-points",
            points_file,
            "--add-points-columns",
            "stp/test:xloc,yloc,zloc",
            str(geom),
        ]
    )
