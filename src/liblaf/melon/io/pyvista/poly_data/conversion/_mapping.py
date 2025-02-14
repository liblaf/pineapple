from collections.abc import Mapping

import glom
import pyvista as pv

from liblaf import melon


class MappingToPolyData(melon.io.AbstractConverter):
    type_from = Mapping
    type_to = pv.PolyData

    def convert(self, obj: Mapping) -> pv.PolyData:
        return pv.PolyData.from_regular_faces(
            obj["points"], glom.glom(obj, glom.Coalesce("faces", "cells"))
        )
