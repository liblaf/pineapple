from typing import Any, NamedTuple

import numpy as np
import pyvista as pv
import trimesh as tm
from jaxtyping import Bool, Float, Integer

from liblaf import melon

from . import InvalidNormalThresholdError


class NearestPointOnSurfaceResult(NamedTuple):
    closest: Float[np.ndarray, "N 3"]
    distance: Float[np.ndarray, " N"]
    triangle_id: Integer[np.ndarray, " N"]


def nearest_point_on_surface(
    source: Any,
    target: Any,
    *,
    distance_threshold: float = 0.1,
    normal_threshold: float = 0.8,
) -> NearestPointOnSurfaceResult:
    need_normals: bool
    if normal_threshold <= -1.0:
        need_normals = False
    elif -1.0 <= normal_threshold <= 1.0:
        need_normals = True
    else:
        raise InvalidNormalThresholdError(normal_threshold)
    source: tm.Trimesh = melon.as_trimesh(source)
    target: pv.PointSet = melon.as_point_set(target, point_normals=need_normals)
    closest: Float[np.ndarray, "N 3"]
    distance: Float[np.ndarray, " N"]
    triangle_id: Integer[np.ndarray, " N"]
    closest, distance, triangle_id = source.nearest.on_surface(target.points)
    invalid_mask: Bool[np.ndarray, " N"] = distance > distance_threshold * source.scale
    if need_normals:
        source_normals: Float[np.ndarray, "N 3"] = source.face_normals[triangle_id]
        target_normals: Float[np.ndarray, "N 3"] = target.point_data["Normals"]
        normal_similarity: Float[np.ndarray, " N"] = np.einsum(
            "ij,ij->i", source_normals, target_normals
        )
        invalid_mask |= normal_similarity < normal_threshold
    closest[invalid_mask] = np.nan
    distance[invalid_mask] = np.inf
    triangle_id[invalid_mask] = -1
    return NearestPointOnSurfaceResult(
        closest=closest, distance=distance, triangle_id=triangle_id
    )
