from pathlib import Path
from typing import Annotated

import numpy as np
import pyvista as pv
import trimesh as tm
import typer
from jaxtyping import Float, Integer
from loguru import logger

import liblaf.grapes as grapes  # noqa: PLR0402
import liblaf.melon as melon  # noqa: PLR0402


def rigid_align(source_file: Path, target_file: Path) -> melon.RigidRegistrationResult:
    source: pv.PolyData = melon.load_poly_data(source_file)
    source_landmarks: Integer[np.ndarray, "L 3"] = melon.load_landmarks(source_file)
    target: pv.PolyData = melon.load_poly_data(target_file)
    target_landmarks: Integer[np.ndarray, "L 3"] = melon.load_landmarks(target_file)
    matrix: Integer[np.ndarray, "4 4"]
    transformed: Float[np.ndarray, "L 3"]
    cost: float
    matrix, transformed, cost = tm.registration.procrustes(
        source_landmarks, target_landmarks
    )
    logger.info("procrustes() > cost: {}", cost)
    rigid: melon.RigidRegistrationResult = melon.rigid_align(
        source, target, init_transform=matrix
    )
    return rigid


def main(
    data_dir: Annotated[Path | None, typer.Option("-d", "--data")] = None,
    output_dir: Annotated[Path | None, typer.Option("-o", "--output")] = None,
) -> None:
    if data_dir is None:
        data_dir = grapes.git.root_safe() / "data/template/wrap/00-raw/"
    if output_dir is None:
        output_dir = grapes.git.root_safe() / "data/template/wrap/01-align/"
    grapes.init_logging()

    # Wrap/face -> SCULPTOR/face
    first_rigid: melon.RigidRegistrationResult = rigid_align(
        data_dir / "wrap/face.obj", data_dir / "sculptor/face.obj"
    )
    # SCULPTOR/cranium -> Wrap/cranium
    second_rigid: melon.RigidRegistrationResult = rigid_align(
        data_dir / "sculptor/cranium.obj", data_dir / "wrap/cranium.obj"
    )
    face: pv.PolyData = melon.load_poly_data(data_dir / "wrap/face.obj")
    transform: Float[np.ndarray, "4 4"] = melon.concat_transforms(
        second_rigid.transformation, first_rigid.transformation
    )
    face = melon.transform(face, transform)
    melon.save(output_dir / "face.ply", face)


if __name__ == "__main__":
    main()
