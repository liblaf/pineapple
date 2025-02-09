from pathlib import Path
from typing import Annotated

import numpy as np
import pyvista as pv
import trimesh as tm
import typer
from jaxtyping import Float
from loguru import logger

import liblaf.grapes as grapes  # noqa: PLR0402
import liblaf.melon as melon  # noqa: PLR0402


def main(
    source_dir: Annotated[
        Path, typer.Option("-s", "--source", exists=True, file_okay=False)
    ] = Path("data/template/00-raw/sculptor"),
    target_dir: Annotated[
        Path, typer.Option("-t", "--target", exists=True, file_okay=False)
    ] = Path("data/template/00-raw/wrap"),
    output_dir: Annotated[Path, typer.Option("-o", "--output", file_okay=False)] = Path(
        "data/template/01-upright/sculptor"
    ),
) -> None:
    grapes.init_logging()
    source_landmarks: Float[np.ndarray, "N 3"] = melon.load_landmarks(
        source_dir / "cranium.landmarks.json"
    )
    target_landmarks: Float[np.ndarray, "N 3"] = melon.load_landmarks(
        target_dir / "cranium.landmarks.json"
    )
    matrix: Float[np.ndarray, "4 4"]
    cost: float
    matrix, _, cost = tm.registration.procrustes(source_landmarks, target_landmarks)
    logger.info("procrustes() > cost: {}", cost)
    for file in source_dir.glob("*.ply"):
        output_file: Path = output_dir / file.name
        mesh: pv.PolyData = melon.load_poly_data(file)
        mesh.transform(matrix, inplace=True)
        melon.save(output_file, mesh)
        landmarks: Float[np.ndarray, "N 3"] = melon.load_landmarks(file)
        landmarks = tm.transform_points(landmarks, matrix)
        melon.save_landmarks(output_file, landmarks)


if __name__ == "__main__":
    typer.run(main)
