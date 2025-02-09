import numpy as np
import pyvista as pv
import trimesh as tm
import typer

import liblaf.grapes as grapes  # noqa: PLR0402
import liblaf.melon as melon  # noqa: PLR0402
from liblaf.melon.typed import StrPath


def load_landmarks(path: StrPath) -> np.ndarray:
    points = grapes.deserialize(path)
    return np.asarray([[p["x"], p["y"], p["z"]] for p in points])


def main() -> None:
    grapes.init_logging()
    source: pv.PolyData = melon.load_poly_data("data/00-raw/template/WrapSkull.obj")
    source_landmarks: np.ndarray = load_landmarks(
        "data/00-raw/template/wrap-skull.landmarks.json"
    )
    target: pv.PolyData = melon.load_poly_data("data/00-raw/template/skull.ply")
    target_landmarks: np.ndarray = load_landmarks(
        "data/00-raw/template/sculptor-mandible.landmarks.json"
    )
    matrix, _, cost = tm.registration.procrustes(source_landmarks, target_landmarks)
    first: pv.PolyData = source.transform(matrix, inplace=False)  # pyright: ignore[reportAssignmentType]
    first.save("data/00-raw/template/WrapSkull-aligned.ply")
    result: melon.RigidRegistrationResult = melon.rigid_align(
        source, target, init_transform=matrix
    )
    ic(result)
    second: pv.PolyData = source.transform(result.transformation, inplace=False)  # pyright: ignore[reportAssignmentType]
    second.save("data/00-raw/template/WrapSkull-aligned2.ply")


if __name__ == "__main__":
    typer.run(main)
