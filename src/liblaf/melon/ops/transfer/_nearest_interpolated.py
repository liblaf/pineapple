from typing import Any, NamedTuple

import attrs
import numpy as np
from jaxtyping import Bool, ScalarLike, Shaped
from numpy.typing import ArrayLike

from . import (
    NearestPointOnSurfaceAuxiliary,
    NearestVertexAuxiliary,
    TransferAlgorithm,
    TransferNearestPointOnSurface,
    TransferNearestVertex,
)


class NearestInterpolatedAuxiliary(NamedTuple):
    nearest_point_on_surface: TransferNearestPointOnSurface
    nearest_point_on_surface_aux: NearestPointOnSurfaceAuxiliary
    nearest_point_on_surface_invalid_mask: Bool[np.ndarray, " target_points"]
    nearest_vertex: TransferNearestVertex
    nearest_vertex_aux: NearestVertexAuxiliary


@attrs.define(frozen=True)
class TransferNearestInterpolated(TransferAlgorithm[NearestInterpolatedAuxiliary]):
    distance_upper_bound: float = 0.1
    max_k: int = 32
    normal_threshold: float = 0.8
    workers: int = -1

    def prepare(self, source: Any, target: Any) -> NearestInterpolatedAuxiliary:
        nearest_point_on_surface = TransferNearestPointOnSurface(
            distance_threshold=self.distance_upper_bound,
            normal_threshold=self.normal_threshold,
        )
        nearest_point_on_surface_aux: NearestPointOnSurfaceAuxiliary = (
            nearest_point_on_surface.prepare(source, target)
        )
        nearest_point_on_surface_invalid_mask: Bool[np.ndarray, " target_points"] = (
            nearest_point_on_surface_aux.triangles[:, 0] == -1
        )
        nearest_vertex = TransferNearestVertex(
            distance_upper_bound=self.distance_upper_bound,
            max_k=self.max_k,
            normal_threshold=self.normal_threshold,
            workers=self.workers,
        )
        nearest_vertex_aux: NearestVertexAuxiliary = nearest_vertex.prepare(
            source, target
        )
        return NearestInterpolatedAuxiliary(
            nearest_point_on_surface=nearest_point_on_surface,
            nearest_point_on_surface_aux=nearest_point_on_surface_aux,
            nearest_point_on_surface_invalid_mask=nearest_point_on_surface_invalid_mask,
            nearest_vertex=nearest_vertex,
            nearest_vertex_aux=nearest_vertex_aux,
        )

    def transfer(
        self,
        aux: NearestInterpolatedAuxiliary,
        data: Shaped[ArrayLike, " source_points *shape"],
        fill_value: ScalarLike | None = None,
    ) -> Shaped[np.ndarray, " target_points *shape"]:
        result: Shaped[np.ndarray, " target_points *shape"] = (
            aux.nearest_point_on_surface.transfer(
                aux.nearest_point_on_surface_aux, data, fill_value
            )
        )
        nearest_vertex_result: Shaped[np.ndarray, " target_points *shape"] = (
            aux.nearest_vertex.transfer(aux.nearest_vertex_aux, data, fill_value)
        )
        result = np.where(
            aux.nearest_point_on_surface_invalid_mask, result, nearest_vertex_result
        )
        return result
