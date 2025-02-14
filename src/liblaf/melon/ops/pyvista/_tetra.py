from typing import Any

import numpy as np
import pyvista as pv
from jaxtyping import Integer

from liblaf import melon


def ensure_positive_volume(mesh: Any) -> pv.UnstructuredGrid:
    mesh: pv.UnstructuredGrid = melon.as_unstructured_grid(mesh)
    mesh = mesh.compute_cell_sizes(
        length=False, area=False, volume=True, vertex_count=False
    )  # pyright: ignore[reportAssignmentType]
    return flip(mesh, mask=mesh.cell_data["Volume"] < 0)


def flip(mesh: Any, mask: Any | None = None) -> pv.UnstructuredGrid:
    mesh: pv.UnstructuredGrid = melon.as_unstructured_grid(mesh)
    cells: Integer[np.ndarray, "C 4"] = mesh.cells_dict[pv.CellType.TETRA]
    if mask is None:
        mask = slice(None)
    cells_new: Integer[np.ndarray, "C 4"] = cells.copy()
    face_to_flip: list[int] = [0, 1, 2]
    cells_new[mask, face_to_flip] = cells[mask, face_to_flip[::-1]]
    return melon.as_unstructured_grid({"points": mesh.points, "tetras": cells_new})
