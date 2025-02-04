from typing import Any

import attrs
import numpy as np
import pyvista as pv
from jaxtyping import Bool, Float, Integer
from scipy.spatial import KDTree

from liblaf import melon


@attrs.frozen
class NearestVertexResult:
    distance: Float[np.ndarray, " N"]
    """(N,) float"""
    missing: Bool[np.ndarray, " N"]
    """(N,) bool"""
    nearest: Float[np.ndarray, " N 3"]
    """(N, 3) float"""
    vertex_id: Integer[np.ndarray, " N"]
    """(N,) int"""


@attrs.frozen
class NearestVertexPrepared:
    distance_threshold: float
    max_k: int
    normal_threshold: float
    workers: int

    source: pv.PointSet
    tree: KDTree

    def query(self, target: Any) -> NearestVertexResult:
        if self.normal_threshold <= -1.0:
            return self._nearest_vertex(target)
        return self._nearest_vertex_with_normal_threshold(target)

    def _nearest_vertex(self, target: Any) -> NearestVertexResult:
        target: pv.PointSet = melon.as_point_set(target)
        distance: Float[np.ndarray, " N"]
        vertex_id: Integer[np.ndarray, " N"]
        distance, vertex_id = self.tree.query(
            target.points,
            distance_upper_bound=self.distance_threshold * self.source.length,
            workers=self.workers,
        )  # pyright: ignore[reportAssignmentType]
        missing: Bool[np.ndarray, " N"] = vertex_id == self.source.n_points
        distance[missing] = np.inf
        vertex_id[missing] = -1
        nearest: Float[np.ndarray, " N 3"] = self.source.points[vertex_id]
        nearest[missing] = np.nan
        return NearestVertexResult(
            distance=distance, missing=missing, nearest=nearest, vertex_id=vertex_id
        )

    def _nearest_vertex_with_normal_threshold(self, target: Any) -> NearestVertexResult:
        source_normals: Float[np.ndarray, "N 3"] = self.source.point_data["Normals"]
        target: pv.PointSet = melon.as_point_set(target, point_normals=True)
        target_normals: Float[np.ndarray, "N 3"] = target.point_data["Normals"]
        result: NearestVertexResult = self._nearest_vertex(target)
        distance: Float[np.ndarray, " N"] = result.distance
        missing: Bool[np.ndarray, " N"] = result.missing
        nearest: Float[np.ndarray, " N 3"] = result.nearest
        vertex_id: Integer[np.ndarray, " N"] = result.vertex_id
        remaining_vertex_id: Integer[np.ndarray, " R"] = missing.nonzero()[0]
        k: int = 2
        while k <= self.max_k and remaining_vertex_id:
            d: Float[np.ndarray, "R k"]
            v: Integer[np.ndarray, "R k"]
            d, v = self.tree.query(
                target.points[remaining_vertex_id],
                k=k,
                distance_upper_bound=self.distance_threshold * self.source.length,
                workers=self.workers,
            )  # pyright: ignore[reportAssignmentType]
            next_remaining_vertex_id: list[int] = []
            for i, vid in enumerate(remaining_vertex_id):
                for j in range(k):
                    if v[i, j] == self.source.n_points:
                        continue
                    normal_similarity: float = np.dot(
                        source_normals[v[i, j]], target_normals[vid]
                    )
                    if normal_similarity < self.normal_threshold:
                        continue
                    distance[vid] = d[i, j]
                    missing[vid] = False
                    vertex_id[vid] = v[i, j]
                    nearest[vid] = self.source.points[v[i, j]]
                    break
                else:
                    next_remaining_vertex_id.append(vid)
            remaining_vertex_id = np.asarray(next_remaining_vertex_id)
            k *= 2
        return NearestVertexResult(
            distance=distance, missing=missing, nearest=nearest, vertex_id=vertex_id
        )


@attrs.frozen
class NearestVertex:
    distance_threshold: float = 0.1
    max_k: int = 32
    normal_threshold: float = attrs.field(
        default=0.8, validator=attrs.validators.le(1.0)
    )
    workers: int = -1

    def prepare(self, source: Any) -> NearestVertexPrepared:
        source: pv.PointSet = melon.as_point_set(
            source, point_normals=self.normal_threshold > -1.0
        )
        tree = KDTree(source.points)
        return NearestVertexPrepared(
            distance_threshold=self.distance_threshold,
            max_k=self.max_k,
            normal_threshold=self.normal_threshold,
            workers=self.workers,
            source=source,
            tree=tree,
        )


def nearest_vertex(
    source: Any,
    target: Any,
    *,
    distance_threshold: float = 0.1,
    max_k: int = 32,
    normal_threshold: float = 0.8,
    workers: int = -1,
) -> NearestVertexResult:
    algorithm = NearestVertex(
        distance_threshold=distance_threshold,
        max_k=max_k,
        normal_threshold=normal_threshold,
        workers=workers,
    )
    prepared: NearestVertexPrepared = algorithm.prepare(source)
    return prepared.query(target)
