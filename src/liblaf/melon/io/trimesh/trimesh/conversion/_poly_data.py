import pyvista as pv
import trimesh as tm

from liblaf import melon


class PolyDataToTrimesh(melon.io.AbstractConverter):
    type_from = pv.PolyData
    type_to = tm.Trimesh

    def convert(self, obj: pv.PolyData) -> tm.Trimesh:
        obj = obj.triangulate()  # pyright: ignore[reportAssignmentType]
        return tm.Trimesh(obj.points, obj.regular_faces)
