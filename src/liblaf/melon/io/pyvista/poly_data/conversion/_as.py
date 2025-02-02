from typing import Any

import pyvista as pv

from liblaf import melon


def as_poly_data(obj: Any) -> pv.PolyData:
    return melon.convert(obj, pv.PolyData)
