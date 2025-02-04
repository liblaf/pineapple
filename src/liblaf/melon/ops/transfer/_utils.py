import numpy as np
from jaxtyping import ScalarLike
from numpy.typing import DTypeLike


def get_fill_value(
    dtype: DTypeLike, fill_value: ScalarLike | None = None
) -> ScalarLike:
    if fill_value is not None:
        return fill_value
    return np.zeros((), dtype=dtype).item()
