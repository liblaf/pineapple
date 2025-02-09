import pyvista as pv

from liblaf import melon


class PolyDataToPointSet(melon.io.AbstractConverter):
    type_from = pv.PolyData
    type_to = pv.PointSet

    def convert(self, obj: pv.PolyData) -> pv.PointSet:
        return obj.cast_to_pointset()
