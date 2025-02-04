from typing import Any

import pyvista as pv

from liblaf import melon
from liblaf.melon.io import conversion_dispatcher


def as_point_set(data: Any, *, point_normals: bool = False) -> pv.PointSet:
    data: pv.PointSet = conversion_dispatcher.convert(data, pv.PointSet)
    if not point_normals:
        return data
    if "Normals" in data.point_data:
        return data
    try:
        mesh: pv.PolyData = melon.as_poly_data(data)
    except melon.io.UnsupportedConversionError:
        pass
    else:
        mesh.point_data["Normals"] = mesh.point_normals
        return data
    # TODO: estimate point normals
    raise NotImplementedError
