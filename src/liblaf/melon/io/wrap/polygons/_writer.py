from pathlib import Path

import numpy as np
from jaxtyping import Integer
from numpy.typing import ArrayLike

import liblaf.grapes as grapes  # noqa: PLR0402
from liblaf.melon.typed import StrPath

from . import get_polygons_path


def save_polygons(path: StrPath, polygons: Integer[ArrayLike, " N"]) -> None:
    path: Path = get_polygons_path(path)
    polygons = np.asarray(polygons)
    grapes.serialize(path, polygons.tolist())
