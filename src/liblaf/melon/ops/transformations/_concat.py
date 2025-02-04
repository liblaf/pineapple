import numpy as np
from jaxtyping import Float
from numpy.typing import ArrayLike


def concat_transforms(
    *transform: Float[ArrayLike, "4 4"] | None,
) -> Float[np.ndarray, "4 4"]:
    result: Float[np.ndarray, "4 4"] = np.eye(4)
    for t in transform:
        if t is None:
            continue
        result = result @ np.asarray(t)
    return result
