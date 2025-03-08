from pathlib import Path

import numpy as np
from jaxtyping import Float

import liblaf.grapes as grapes  # noqa: PLR0402
from liblaf.melon.typed import StrPath

from . import get_landmarks_path


def load_landmarks(path: StrPath) -> Float[np.ndarray, "N 3"]:
    path: Path = get_landmarks_path(path)
    data: list[dict[str, float]] = grapes.load_json(path)
    return np.asarray([[p["x"], p["y"], p["z"]] for p in data])
