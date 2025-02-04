from typing import Any, NamedTuple

import numpy as np
import pyvista as pv
from jaxtyping import Float, Integer
from scipy.spatial import KDTree

from liblaf import melon

from . import InvalidNormalThresholdError


class NearestVertexResult(NamedTuple):
    distance: Float[np.ndarray, " N"]
    vertex_id: Integer[np.ndarray, " N"]


def nearest_vertex(
    source: Any,
    target: Any,
    *,
    distance_upper_bound: float = 0.1,
    max_k: int = 32,
    normal_threshold: float = 0.8,
    workers: int = -1,
) -> NearestVertexResult:
    if normal_threshold <= -1.0:
        return _nearest_vertex(
            source, target, distance_upper_bound=distance_upper_bound, workers=workers
        )
    if -1.0 <= normal_threshold <= 1.0:
        return _nearest_vertex_with_normal_threshold(
            source,
            target,
            distance_upper_bound=distance_upper_bound,
            max_k=max_k,
            normal_threshold=normal_threshold,
            workers=workers,
        )
    raise InvalidNormalThresholdError(normal_threshold)


def _nearest_vertex(
    source: Any, target: Any, *, distance_upper_bound: float, workers: int
) -> NearestVertexResult:
    source: pv.PointSet = melon.as_point_set(source)
    target: pv.PointSet = melon.as_point_set(target)
    tree = KDTree(source.points)
    distance: Float[np.ndarray, " N"]
    vertex_id: Integer[np.ndarray, " N"]
    distance, vertex_id = tree.query(
        target.points,
        distance_upper_bound=distance_upper_bound * source.length,
        workers=workers,
    )  # pyright: ignore[reportAssignmentType]
    vertex_id[vertex_id == source.n_points] = -1
    return NearestVertexResult(distance=distance, vertex_id=vertex_id)


def _nearest_vertex_with_normal_threshold(
    source: Any,
    target: Any,
    *,
    distance_upper_bound: float,
    max_k: int,
    normal_threshold: float,
    workers: int,
) -> NearestVertexResult:
    source: pv.PointSet = melon.as_point_set(source, point_normals=True)
    source_normals: Float[np.ndarray, "N 3"] = source.point_data["Normals"]
    target: pv.PointSet = melon.as_point_set(target, point_normals=True)
    target_normals: Float[np.ndarray, "N 3"] = target.point_data["Normals"]
    max_k = min(max_k, source.n_points)
    tree = KDTree(source.points)
    distance: Float[np.ndarray, " N"]
    vertex_id: Integer[np.ndarray, " N"]
    distance, vertex_id = _nearest_vertex(
        source, target, distance_upper_bound=distance_upper_bound, workers=workers
    )
    remaining_vertex_id: list[int] = list(np.where(vertex_id == -1)[0])
    k: int = 2
    while k <= max_k and remaining_vertex_id:
        d: Float[np.ndarray, "remaining_vertices k"]
        v: Integer[np.ndarray, "remaining_vertices k"]
        d, v = tree.query(
            target.points[remaining_vertex_id],
            k=k,
            distance_upper_bound=distance_upper_bound * source.length,
            workers=workers,
        )  # pyright: ignore[reportAssignmentType]
        next_remaining_vertex_id: list[int] = []
        for i, vid in enumerate(remaining_vertex_id):
            for j in range(k):
                if v[i, j] == source.n_points:
                    continue
                normal_similarity: float = np.dot(
                    source_normals[v[i, j]], target_normals[vid]
                )
                if normal_similarity < normal_threshold:
                    continue
                distance[vid] = d[i, j]
                vertex_id[vid] = v[i, j]
                break
            else:
                next_remaining_vertex_id.append(vid)
        k *= 2
    return NearestVertexResult(distance=distance, vertex_id=vertex_id)
