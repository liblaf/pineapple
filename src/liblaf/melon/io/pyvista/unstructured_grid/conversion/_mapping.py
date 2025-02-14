from collections.abc import Mapping

import glom
import pyvista as pv

from liblaf import melon


class MappingToUnstructuredGrid(melon.io.AbstractConverter):
    type_from = Mapping
    type_to = pv.UnstructuredGrid

    def convert(self, obj: Mapping) -> pv.UnstructuredGrid:
        return pv.UnstructuredGrid(
            {pv.CellType.TETRA: glom.glom(obj, glom.Coalesce("tetras", "cells"))},
            obj["points"],
        )
