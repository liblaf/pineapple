from typing import Any

import attrs
import numpy as np
import pyvista as pv
import trimesh as tm
from jaxtyping import Bool, Float
from loguru import logger
from numpy.typing import ArrayLike

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

    def register(
        self, source: Any, target: Any, *, init_transform: Float[ArrayLike, "4 4"]
    ) -> RigidRegistrationResult:
        corresp_algo_prepared: melon.NearestVertexPrepared = self.corresp_algo.prepare(
            target
        )
        source: pv.PolyData = melon.as_poly_data(source)
        target: pv.PolyData = melon.as_poly_data(target)
        init_transform: Float[np.ndarray, "4 4"] = np.asarray(init_transform)
        result = RigidRegistrationResult(
            init_transform=init_transform,
            loss=np.nan,
            transformation=init_transform,
            history=[np.eye(4)],
        )
        source_weights: Float[np.ndarray, " N"] | None = source.point_data.get(
            "Weights"
        )
        target_weights: Float[np.ndarray, " N"] | None = target.point_data.get(
            "Weights"
        )
        for it in range(self.max_iters):
            transformed: pv.PolyData = source.transform(
                result.transformation, inplace=False
            )  # pyright: ignore[reportAssignmentType]
            corresp: melon.NearestVertexResult = corresp_algo_prepared.query(
                transformed
            )
            valid_mask: Bool[np.ndarray, " N"] = ~corresp.missing
            matrix: Float[np.ndarray, "4 4"]
            cost: float
            source_points: Float[np.ndarray, "N 3"] = transformed.points[valid_mask]
            target_points: Float[np.ndarray, "N 3"] = corresp.nearest[valid_mask]
            weights: Float[np.ndarray, " N"] = np.ones((source_points.shape[0],))
            if source_weights:
                weights *= source_weights[valid_mask]
            if target_weights:
                weights *= target_weights[corresp.vertex_id[valid_mask]]
            matrix, _, cost = tm.registration.procrustes(
                source_points,
                target_points,
                weights=weights,
                reflection=self.reflection,
                translation=self.translation,
                scale=self.scale,
                return_cost=True,
            )
            last_loss: float = result.loss
            result.loss = cost
            result.transformation = matrix @ result.transformation
            result.history.append(result.transformation)
            # log loss metric
            logger.debug("ICP (it: {}) > loss: {}", it, cost)
            if last_loss - cost < self.loss_threshold:
                break
        return result
