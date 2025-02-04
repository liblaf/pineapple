from typing import Any
from venv import logger

import attrs
import numpy as np
import pyvista as pv
import trimesh as tm
from jaxtyping import Bool, Float

from liblaf import melon

from . import RigidRegistrationAlgorithm, RigidRegistrationResult


@attrs.frozen
class RigidICP(RigidRegistrationAlgorithm):
    loss_threshold: float = 1e-6
    max_iters: int = 100
    reflection: bool = False
    scale: bool = True
    translation: bool = True
    corresp_algo: melon.NearestVertex = attrs.field(factory=melon.NearestVertex)

    def register(self, source: Any, target: Any) -> RigidRegistrationResult:
        corresp_algo_prepared: melon.NearestVertexPrepared = self.corresp_algo.prepare(
            target
        )
        source: pv.PolyData = melon.as_poly_data(source)
        target: pv.PolyData = melon.as_poly_data(target)
        result: RigidRegistrationResult = RigidRegistrationResult(
            loss=np.nan, transformation=np.eye(4)
        )
        source_weights: Float[np.ndarray, " N"] | None = source.point_data.get(
            "Weights"
        )
        target_weights: Float[np.ndarray, " N"] | None = target.point_data.get(
            "Weights"
        )
        for it in range(self.max_iters):
            corresp: melon.NearestVertexResult = corresp_algo_prepared.query(target)
            valid_mask: Bool[np.ndarray, " N"] = ~corresp.missing
            matrix: Float[np.ndarray, "4 4"]
            cost: float
            source_points: Float[np.ndarray, "N 3"] = source.points[valid_mask]
            target_points: Float[np.ndarray, "N 3"] = corresp.nearest[valid_mask]
            weights: Float[np.ndarray, " N"] = np.ones(source_points.shape[0])
            if source_weights:
                weights *= source_weights[valid_mask]
            if target_weights:
                weights *= target_weights[valid_mask]
            matrix, _, cost = tm.registration.procrustes(
                source_points,
                target_points,
                weights=weights,
                reflection=self.reflection,
                translation=self.translation,
                scale=self.scale,
                return_cost=True,
            )
            result.transformation = matrix @ result.transformation
            logger.debug("ICP ({}) > loss = {}", it, cost)
            if result.loss - cost < self.loss_threshold:
                break
            result.loss = cost
            source = source.transform(matrix, inplace=True)  # pyright: ignore[reportAssignmentType]
        return result
