from pathlib import Path
from typing import Annotated

import numpy as np
import pyvista as pv
import trimesh as tm
import typer
from jaxtyping import Float

import liblaf.grapes as grapes  # noqa: PLR0402
from liblaf import melon


def main(
    source_file: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    target_file: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    *,
    output_file: Annotated[Path, typer.Option("-o", "--output", dir_okay=False)],
) -> None:
    grapes.init_logging()
    source: pv.PolyData = melon.load_poly_data(source_file)
    target: pv.PolyData = melon.load_poly_data(target_file)
    source_landmarks: Float[np.ndarray, "N 3"] = melon.load_landmarks(source_file)
    target_landmarks: Float[np.ndarray, "N 3"] = melon.load_landmarks(target_file)
    init_transform: Float[np.ndarray, "4 4"]
    cost: float
    init_transform, _, cost = tm.registration.procrustes(
        source_landmarks, target_landmarks
    )
    result: melon.RigidRegistrationResult = melon.rigid_align(
        source, target, init_transform=init_transform
    )
    transformed: pv.PolyData = source.transform(result.transformation)  # pyright: ignore[reportAssignmentType]
    transformed_landmarks: Float[np.ndarray, "N 3"] = tm.transform_points(
        source_landmarks, result.transformation
    )
    melon.save(output_file, transformed)
    melon.save_landmarks(output_file, transformed_landmarks)


if __name__ == "__main__":
    typer.run(main)
