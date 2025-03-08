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


def main(data_dir: Annotated[Path | None, typer.Option("-d", "--data")] = None) -> None:
    if data_dir is None:
        data_dir = grapes.git.root_safe() / "data/template/00-raw/"
    grapes.init_logging()
    source_face: pv.PolyData = melon.load_poly_data(data_dir / "wrap/face.obj")
    source_face_landmarks: Integer[np.ndarray, "L 3"] = melon.load_landmarks(
        data_dir / "wrap/face.landmarks.json"
    )
    target_face: pv.PolyData = melon.load_poly_data(data_dir / "sculptor/face.obj")
    target_face_landmarks: Integer[np.ndarray, "L 3"] = melon.load_landmarks(
        data_dir / "sculptor/face.landmarks.json"
    )
    matrix: Integer[np.ndarray, "4 4"]
    transformed: Float[np.ndarray, "L 3"]
    cost: float
    matrix, transformed, cost = tm.registration.procrustes(
        source_face_landmarks, target_face_landmarks
    )
    logger.info("procrustes() > cost: {}", cost)
    rigid: melon.RigidRegistrationResult = melon.rigid_align(
        source_face, target_face, init_transform=matrix
    )
    result: pv.PolyData = melon.transform(source_face, rigid.transformation)
    result.field_data["transform"] = rigid.transformation
    melon.save("data/face.ply", result)


if __name__ == "__main__":
    main()
