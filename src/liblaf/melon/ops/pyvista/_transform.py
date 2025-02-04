from typing import Any

import numpy as np
import pyvista as pv
from jaxtyping import Float
from numpy.typing import ArrayLike

from liblaf import melon


def transform(
    data: Any,
    trans: Float[ArrayLike, "4 4"] | None,
    *,
    transform_all_input_vectors: bool = False,
) -> pv.PolyData:
    if trans is None:
        return data
    trans: Float[np.ndarray, "4 4"] = np.asarray(trans)
    data: pv.PolyData = melon.as_poly_data(data)
    data = data.transform(
        trans, transform_all_input_vectors=transform_all_input_vectors, inplace=False
    )  # pyright: ignore[reportAssignmentType]
    return data
