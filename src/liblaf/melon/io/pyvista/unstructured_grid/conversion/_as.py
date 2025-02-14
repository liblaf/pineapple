from typing import Any

import pyvista as pv

from liblaf.melon.io import conversion_dispatcher

from . import MappingToUnstructuredGrid

conversion_dispatcher.register(MappingToUnstructuredGrid())


def as_unstructured_grid(obj: Any) -> pv.UnstructuredGrid:
    return conversion_dispatcher.convert(obj, pv.UnstructuredGrid)
