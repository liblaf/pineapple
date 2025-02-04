from typing import Any

import attrs
import numpy as np
import trimesh as tm
from jaxtyping import Bool, Float, Integer, ScalarLike, Shaped
from numpy.typing import ArrayLike

from liblaf import melon

from . import TransferAlgorithm, TransferAlgorithmPrepared


@attrs.frozen
class TransferNearestPointOnSurfacePrepared(TransferAlgorithmPrepared):
    barycentric: Float[np.ndarray, "target_points 3"]
    missing: Bool[np.ndarray, " target_points"]
    triangles: Integer[np.ndarray, "target_points 3"]

    def transfer(
        self, data: Shaped[ArrayLike, "source_points ..."], fill_value: ScalarLike
    ) -> Float[np.ndarray, "target_points ..."]:
        data: Float[np.ndarray, "source_points ..."] = np.asarray(data)
        result: Float[np.ndarray, "target_points ..."] = np.einsum(
            "ij,ij...->i...", self.barycentric, data[self.triangles], dtype=data.dtype
        )
        result[self.missing] = fill_value
        return result


@attrs.frozen
class TransferNearestPointOnSurface(TransferAlgorithm):
    distance_threshold: float = 0.1
    normal_threshold: float = 0.8

    def prepare(
        self, source: Any, target: Any
    ) -> TransferNearestPointOnSurfacePrepared:
        source: tm.Trimesh = melon.as_trimesh(source)
        corresp: melon.NearestPointOnSurfaceResult = melon.nearest_point_on_surface(
            source,
            target,
            distance_threshold=self.distance_threshold,
            normal_threshold=self.normal_threshold,
        )
        triangles: Integer[np.ndarray, "target_points 3"] = source.faces[
            corresp.triangle_id
        ]
        barycentric: Float[np.ndarray, "target_points 3"] = (
            tm.triangles.points_to_barycentric(
                source.vertices[triangles], corresp.nearest
            )
        )
        barycentric[corresp.missing] = np.nan
        triangles[corresp.missing] = -1
        return TransferNearestPointOnSurfacePrepared(
            barycentric=barycentric, missing=corresp.missing, triangles=triangles
        )
