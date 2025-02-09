from collections.abc import Mapping

import pyvista as pv

from liblaf import melon


class MappingToPolyData(melon.io.AbstractConverter):
    type_from = Mapping
    type_to = pv.PolyData

    def convert(self, obj: Mapping) -> pv.PolyData:
        return pv.PolyData.from_regular_faces(
            obj["points"], obj.get("faces") or obj["cells"]
        )
