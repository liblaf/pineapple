from collections.abc import Sequence
from typing import Any, Literal

import pyvista as pv
from jaxtyping import Float
from numpy.typing import ArrayLike

from liblaf import melon


def contour(
    data: Any,
    isosurfaces: int | Sequence[float] | None = None,
    scalars: str | Float[ArrayLike, "..."] | None = None,
    *,
    compute_normals: bool = False,
    compute_gradients: bool = False,
    compute_scalars: bool = True,
    rng: Sequence[float] | None = None,
    preference: Literal["point", "cell"] = "point",
    method: Literal["contour", "marching_cubes", "flying_edges"] = "contour",
    progress_bar: bool = False,
) -> pv.PolyData:
    data: pv.ImageData = melon.as_image_data(data)
    result: pv.PolyData = data.contour(  # pyright: ignore[reportAssignmentType]
        isosurfaces=isosurfaces,  # pyright: ignore[reportArgumentType]
        scalars=scalars,
        compute_normals=compute_normals,
        compute_gradients=compute_gradients,
        compute_scalars=compute_scalars,
        rng=rng,
        preference=preference,
        method=method,
        progress_bar=progress_bar,
    )
    return result
