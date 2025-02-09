from collections.abc import Iterable, Sequence
from typing import Any

import numpy as np
import pyvista as pv
from jaxtyping import Integer

from liblaf import melon


def select_cells_by_group(
    mesh: Any, groups: int | str | Iterable[int | str] | None = None
) -> Integer[np.ndarray, " N"]:
    mesh: pv.PolyData = melon.as_poly_data(mesh)
    names: Sequence[str] | None = mesh.field_data.get("GroupNames")  # pyright: ignore[reportAssignmentType]
    groups: list[int | str] = _get_groups(groups, names)


def _get_group_ids(
    groups: int | str | Iterable[int | str] | None, names: Sequence[str] | None
) -> list[int]:
    if groups is None:
        return list(range(len(names)))
    if isinstance(groups, int | str):
        groups = [groups]
    return [_get_group_id(group, names) for group in groups]


def _get_group_id(group: int | str, names: Sequence[str] | None = None) -> int:
    if isinstance(group, int):
        return group
    if names is None:
        msg = "Group names are not available."
        raise ValueError(msg)
    return names.index(group)
