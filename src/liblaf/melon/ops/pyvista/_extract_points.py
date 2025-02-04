from typing import Any

import pyvista as pv
from jaxtyping import Bool, Integer
from numpy.typing import ArrayLike

from liblaf import melon


def extract_points(
    data: Any, ind: Bool[ArrayLike, " N"] | Integer[ArrayLike, " N"]
) -> pv.PointSet:
    data: pv.PointSet = melon.as_point_set(data)
    unstructured: pv.UnstructuredGrid = data.extract_points(ind)  # pyright: ignore[reportAssignmentType]
    return melon.as_point_set(unstructured)
