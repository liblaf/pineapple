from typing import Any, NamedTuple

import attrs
import numpy as np
import trimesh as tm
from jaxtyping import Bool, Float, Integer, ScalarLike
from numpy.typing import ArrayLike

from liblaf import melon

from . import TransferAlgorithm


class NearestPointOnSurfaceAuxiliary(NamedTuple):
    barycentric: Float[np.ndarray, "target_points 3"]
    triangles: Integer[np.ndarray, "target_points 3"]


@attrs.define(frozen=True)
class TransferNearestPointOnSurface(TransferAlgorithm[NearestPointOnSurfaceAuxiliary]):
    distance_threshold: float = 0.1
    normal_threshold: float = 0.8

    def prepare(self, source: Any, target: Any) -> NearestPointOnSurfaceAuxiliary:
        source: tm.Trimesh = melon.as_trimesh(source)
        closest: Float[np.ndarray, "target_points 3"]
        triangle_id: Integer[np.ndarray, " target_points"]
        closest, _, triangle_id = melon.nearest_point_on_surface(
            source,
            target,
            distance_threshold=self.distance_threshold,
            normal_threshold=self.normal_threshold,
        )
        invalid_mask: Bool[np.ndarray, " target_points"] = triangle_id == -1
        triangles: Integer[np.ndarray, "target_points 3"] = source.faces[triangle_id]
        barycentric: Float[np.ndarray, "target_points 3"] = (
            tm.triangles.points_to_barycentric(source.vertices[triangles], closest)
        )
        barycentric[invalid_mask] = np.nan
        triangles[invalid_mask] = -1
        return NearestPointOnSurfaceAuxiliary(
            barycentric=barycentric, triangles=triangles
        )

    def transfer(
        self,
        aux: NearestPointOnSurfaceAuxiliary,
        data: Float[ArrayLike, "source_points ..."],
        fill_value: ScalarLike | None = None,
    ) -> Float[np.ndarray, "target_points ..."]:
        data: Float[np.ndarray, "source_points ..."] = np.asarray(data)
        valid_mask: Bool[np.ndarray, " target_points"] = aux.triangles[:, 0] != -1
        result: Float[np.ndarray, "target_points ..."]
        if valid_mask.all():
            result = np.einsum(
                "ij,ij...->i...", aux.barycentric, data[aux.triangles], dtype=data.dtype
            )
        else:
            result = np.full(
                (aux.triangles.shape[0], *data.shape[1:]),
                fill_value,
                dtype=data.dtype,
            )
            result[valid_mask] = np.einsum(
                "ij,ij...->i...",
                aux.barycentric[valid_mask],
                data[aux.triangles[valid_mask]],
            )
        return result
