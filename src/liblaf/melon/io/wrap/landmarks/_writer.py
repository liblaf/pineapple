from pathlib import Path

import numpy as np
from jaxtyping import Float
from numpy.typing import ArrayLike

import liblaf.grapes as grapes  # noqa: PLR0402
from liblaf.melon.typed import StrPath

from . import get_landmarks_path


def save_landmarks(path: StrPath, points: Float[ArrayLike, "N 3"]) -> None:
    path: Path = get_landmarks_path(path)
    points: Float[np.ndarray, "N 3"] = np.asarray(points)
    data: list[dict[str, float]] = [{"x": p[0], "y": p[1], "z": p[2]} for p in points]
    grapes.serialize(path, data)
