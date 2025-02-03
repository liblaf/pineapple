from collections.abc import Sequence
from typing import Any

import pyvista as pv

from liblaf import melon


def gaussian_smooth(
    data: Any,
    radius_factor: float | Sequence[float] = 1.5,
    std_dev: float | Sequence[float] = 2.0,
    scalars: str | None = None,
    *,
    progress_bar: bool = False,
) -> pv.ImageData:
    data: pv.ImageData = melon.as_image_data(data)
    result: pv.ImageData = data.gaussian_smooth(  # pyright: ignore[reportAssignmentType]
        radius_factor=radius_factor,  # pyright: ignore[reportArgumentType]
        std_dev=std_dev,  # pyright: ignore[reportArgumentType]
        scalars=scalars,
        progress_bar=progress_bar,
    )
    return result
