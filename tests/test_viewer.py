from __future__ import annotations

import json
from pathlib import Path

import pytest
from lgdo import Array, Table, VectorOfVectors, lh5
from pyg4ometry import gdml

from pygeomtools import viewer


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
