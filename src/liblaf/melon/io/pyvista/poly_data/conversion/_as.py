from typing import Any

import pyvista as pv

from liblaf.melon.io import conversion_dispatcher

from . import MappingToPolyData

conversion_dispatcher.register(MappingToPolyData())


def as_poly_data(obj: Any) -> pv.PolyData:
    return conversion_dispatcher.convert(obj, pv.PolyData)
