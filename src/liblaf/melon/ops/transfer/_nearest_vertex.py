from typing import Any

import attrs
import numpy as np
from jaxtyping import Bool, Integer, Num, ScalarLike, Shaped
from numpy.typing import ArrayLike

from liblaf import melon

from . import TransferAlgorithm, TransferAlgorithmPrepared


@attrs.frozen
class TransferNearestVertexPrepared(TransferAlgorithmPrepared):
    missing: Bool[np.ndarray, " target_points"]
    vertex_id: Integer[np.ndarray, " target_points"]

    def transfer(
        self, data: Shaped[ArrayLike, "source_points ..."], fill_value: ScalarLike
    ) -> Any:
        data: Num[np.ndarray, "source_points ..."] = np.asarray(data)
        result: Shaped[np.ndarray, "target_points ..."] = data[self.vertex_id].copy()
        result[self.missing] = fill_value
        return result


@attrs.frozen
class TransferNearestVertex(TransferAlgorithm):
    distance_upper_bound: float = 0.1
    max_k: int = 32
    normal_threshold: float = 0.8
    workers: int = -1

    def prepare(self, source: Any, target: Any) -> TransferNearestVertexPrepared:
        corresp: melon.NearestVertexResult = melon.nearest_vertex(
            source,
            target,
            distance_threshold=self.distance_upper_bound,
            max_k=self.max_k,
            normal_threshold=self.normal_threshold,
            workers=self.workers,
        )
        return TransferNearestVertexPrepared(
            missing=corresp.missing, vertex_id=corresp.vertex_id
        )
