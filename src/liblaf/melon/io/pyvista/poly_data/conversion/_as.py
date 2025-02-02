from typing import Any

import pyvista as pv

from liblaf.melon.io import conversion_dispatcher


def as_poly_data(obj: Any) -> pv.PolyData:
    return conversion_dispatcher.convert(obj, pv.PolyData)
