from collections.abc import Mapping

import glom
import numpy as np
import pyvista as pv
from jaxtyping import Integer

from liblaf import melon


class MappingToUnstructuredGrid(melon.io.AbstractConverter):
    type_from = Mapping
    type_to = pv.UnstructuredGrid

    def convert(self, obj: Mapping) -> pv.UnstructuredGrid:
        cell_array: pv.CellArray = pv.CellArray.from_regular_cells(
            glom.glom(obj, glom.Coalesce("tetras", "cells"))
        )
        cell_type: Integer[np.ndarray, " C"] = np.full(
            (cell_array.n_cells,), pv.CellType.TETRA
        )
        return pv.UnstructuredGrid(cell_array.cells, cell_type, obj["points"])
