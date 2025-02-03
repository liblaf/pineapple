from typing import Any

import pyvista as pv

from liblaf.melon.io import conversion_dispatcher


def as_image_data(data: Any) -> pv.ImageData:
    return conversion_dispatcher.convert(data, pv.ImageData)
