from typing import Any, NamedTuple

import attrs
import numpy as np
from jaxtyping import Bool, Integer, Num, ScalarLike
from numpy.typing import ArrayLike

from liblaf import melon

from . import TransferAlgorithm


class NearestVertexAuxiliary(NamedTuple):
    vertex_id: Integer[np.ndarray, " target_points"]


@attrs.define(frozen=True)
class TransferNearestVertex(TransferAlgorithm[NearestVertexAuxiliary]):
    distance_upper_bound: float = 0.1
    max_k: int = 32
    normal_threshold: float = 0.8
    workers: int = -1

    def prepare(self, source: Any, target: Any) -> NearestVertexAuxiliary:
        vertex_id: Integer[np.ndarray, " target_points"]
        _, vertex_id = melon.nearest_vertex(
            source,
            target,
            distance_upper_bound=self.distance_upper_bound,
            max_k=self.max_k,
            normal_threshold=self.normal_threshold,
            workers=self.workers,
        )
        return NearestVertexAuxiliary(vertex_id=vertex_id)

    def transfer(
        self,
        aux: NearestVertexAuxiliary,
        data: Num[ArrayLike, "source_points ..."],
        fill_value: ScalarLike | None = None,
    ) -> Any:
        data: Num[np.ndarray, "source_points ..."] = np.asarray(data)
        vertex_id: Integer[np.ndarray, " target_points"] = aux.vertex_id
        valid_mask: Bool[np.ndarray, " target_points"] = vertex_id != -1
        if valid_mask.all():
            return data[vertex_id]
        result: Num[np.ndarray, "target_points ..."] = np.full(
            (vertex_id.shape[0], *data.shape[1:]), fill_value, dtype=data.dtype
        )
        result[valid_mask] = data[vertex_id[valid_mask]]
        return result
