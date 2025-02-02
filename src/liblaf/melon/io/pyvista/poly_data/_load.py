from pathlib import Path

import pyvista as pv

from liblaf.melon.typing import StrPath


def load_poly_data(path: StrPath) -> pv.PolyData:
    path = Path(path)
    return pv.read(path)  # pyright: ignore[reportReturnType]
