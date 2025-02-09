import importlib.resources
import string
import subprocess as sp
import tempfile
from pathlib import Path
from typing import Any

import pyvista as pv
from jaxtyping import Float, Integer
from numpy.typing import ArrayLike

from liblaf import melon


def fast_wrapping(
    source: Any,
    target: Any,
    *,
    source_landmarks: Float[ArrayLike, "N 3"] | None = None,
    target_landmarks: Float[ArrayLike, "N 3"] | None = None,
    free_polygons_floating: Integer[ArrayLike, " N"] | None = None,
) -> pv.PolyData:
    source_landmarks = source_landmarks if source_landmarks is not None else []
    target_landmarks = target_landmarks if target_landmarks is not None else []
    free_polygons_floating = (
        free_polygons_floating if free_polygons_floating is not None else []
    )
    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir: Path = Path(tmpdir_str).absolute()
        source_path: Path = tmpdir / "source.obj"
        target_path: Path = tmpdir / "target.obj"
        output_path: Path = tmpdir / "output.obj"
        source_landmarks_path: Path = tmpdir / "source.landmarks.json"
        target_landmarks_path: Path = tmpdir / "target.landmarks.json"
        free_polygons_floating_path: Path = tmpdir / "free-polygons-floating.json"
        melon.save(source_path, source)
        melon.save(target_path, target)
        melon.save_landmarks(source_landmarks_path, source_landmarks)
        melon.save_landmarks(target_landmarks_path, target_landmarks)
        melon.save_polygons(free_polygons_floating_path, free_polygons_floating)
        template = string.Template(
            (
                importlib.resources.files("liblaf.melon.plugin.wrap.resources")
                / "fast-wrapping.wrap"
            ).read_text()
        )
        project: str = template.substitute(
            {
                "BASEMESH": str(source_path),
                "SCAN": str(target_path),
                "OUTPUT": str(output_path),
                "LEFT_LANDMARKS": str(source_landmarks_path),
                "RIGHT_LANDMARKS": str(target_landmarks_path),
                "FREE_POLYGONS_FLOATING": str(free_polygons_floating_path),
            }
        )
        project_path: Path = tmpdir / "project.wrap"
        project_path.write_text(project)
        sp.run(["WrapCmd.sh", "compute", project_path], check=True)
        return melon.load_poly_data(output_path)
