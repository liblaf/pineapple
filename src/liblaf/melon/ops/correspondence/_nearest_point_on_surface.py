import functools
from typing import Any

import attrs
import numpy as np
import pyvista as pv
import trimesh as tm
from jaxtyping import Bool, Float, Integer
from numpy.typing import ArrayLike

from liblaf import melon

from . import NearestVertex, NearestVertexPrepared


@attrs.frozen
class NearestPointOnSurfaceResult:
    distance: Float[np.ndarray, " N"]
    """(N,) float"""
    missing: Bool[np.ndarray, " N"]
    """(N,) bool"""
    nearest: Float[np.ndarray, "N 3"]
    """(N, 3) float"""
    triangle_id: Integer[np.ndarray, " N"]
    """(N,) int"""


@attrs.frozen
class NearestPointOnSurfacePrepared:
    distance_threshold: float
    fallback_to_nearest_vertex: bool
    max_k: int
    normal_threshold: float
    workers: int

    source: tm.Trimesh

    def query(self, target: Any) -> NearestPointOnSurfaceResult:
        need_normals: bool = self.normal_threshold > -1.0
        target: pv.PointSet = melon.as_point_set(target, point_normals=need_normals)
        nearest: Float[np.ndarray, "N 3"]
        distance: Float[np.ndarray, " N"]
        triangle_id: Integer[np.ndarray, " N"]
        nearest, distance, triangle_id = self.source.nearest.on_surface(target.points)
        missing: Bool[np.ndarray, " N"] = (
            distance > self.distance_threshold * self.source.scale
        )
        if need_normals:
            source_normals: Float[np.ndarray, "N 3"] = self.source.face_normals[
                triangle_id
            ]
            target_normals: Float[np.ndarray, "N 3"] = target.point_data["Normals"]
            normal_similarity: Float[np.ndarray, " N"] = np.vecdot(
                source_normals, target_normals
            )
            missing |= normal_similarity < self.normal_threshold
        distance[missing] = np.inf
        nearest[missing] = np.nan
        triangle_id[missing] = -1
        result = NearestPointOnSurfaceResult(
            distance=distance, missing=missing, nearest=nearest, triangle_id=triangle_id
        )
        if self.fallback_to_nearest_vertex:
            result = self._fallback_to_nearest_vertex(target, result)
        return result

    @functools.cached_property
    def _nearest_vertex(self) -> NearestVertexPrepared:
        return NearestVertex(
            distance_threshold=self.distance_threshold,
            max_k=self.max_k,
            normal_threshold=self.normal_threshold,
            workers=self.workers,
        ).prepare(self.source)

    def _fallback_to_nearest_vertex(
        self, target: pv.PointSet, result: NearestPointOnSurfaceResult
    ) -> NearestPointOnSurfaceResult:
        missing_vid: Integer[np.ndarray, " N"] = result.missing.nonzero()[0]
        remaining: pv.PointSet = target.extract_points(missing_vid, include_cells=False)  # pyright: ignore[reportAssignmentType]
        remaining_result: melon.NearestVertexResult = self._nearest_vertex.query(
            remaining
        )
        result.distance[result.missing] = remaining_result.distance
        result.missing[result.missing] = remaining_result.missing
        result.nearest[result.missing] = remaining_result.nearest
        result.triangle_id[result.missing] = self._vertex_id_to_triangle_id(
            remaining_result.vertex_id
        )
        return result

    def _vertex_id_to_triangle_id(
        self, vertex_id: Integer[ArrayLike, " N"]
    ) -> Integer[np.ndarray, " N"]:
        return self.source.vertex_faces[vertex_id, 0]


@attrs.frozen
class NearestPointOnSurface:
    distance_threshold: float = 0.1
    fallback_to_nearest_vertex: bool = False
    max_k: int = 32
    normal_threshold: float = attrs.field(
        default=0.8, validator=attrs.validators.le(1.0)
    )
    workers: int = -1

    def prepare(self, source: Any) -> NearestPointOnSurfacePrepared:
        source: tm.Trimesh = melon.as_trimesh(source)
        return NearestPointOnSurfacePrepared(
            distance_threshold=self.distance_threshold,
            fallback_to_nearest_vertex=self.fallback_to_nearest_vertex,
            max_k=self.max_k,
            normal_threshold=self.normal_threshold,
            workers=self.workers,
            source=source,
        )


def nearest_point_on_surface(
    source: Any,
    target: Any,
    *,
    distance_threshold: float = 0.1,
    fallback_to_nearest_vertex: bool = False,
    max_k: int = 32,
    normal_threshold: float = 0.8,
    workers: int = -1,
) -> NearestPointOnSurfaceResult:
    algorithm = NearestPointOnSurface(
        distance_threshold=distance_threshold,
        fallback_to_nearest_vertex=fallback_to_nearest_vertex,
        max_k=max_k,
        normal_threshold=normal_threshold,
        workers=workers,
    )
    prepared: NearestPointOnSurfacePrepared = algorithm.prepare(source)
    return prepared.query(target)
