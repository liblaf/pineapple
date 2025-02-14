from collections.abc import Container
from pathlib import Path

import pyvista as pv

from liblaf import melon
from liblaf.melon.typed import StrPath

from . import load_obj


def load_poly_data(path: StrPath) -> pv.PolyData:
    path = Path(path)
    if path.suffix == ".obj":
        return load_obj(path)
    return pv.read(path)  # pyright: ignore[reportReturnType]


class PolyDataReader(melon.io.AbstractReader):
    extensions: Container[str] = {".obj", ".stl", ".vtp", ".ply"}

    def load(self, path: StrPath) -> pv.PolyData:
        return load_poly_data(path)
