from pathlib import Path

import pyvista as pv

from liblaf import melon
from liblaf.melon.typing import StrPath


def load_poly_data(path: StrPath) -> pv.PolyData:
    path = Path(path)
    return pv.read(path)  # pyright: ignore[reportReturnType]


class PolyDataReader(melon.io.AbstractReader):
    def match_path(self, path: StrPath) -> bool:
        path = Path(path)
        return path.suffix in {
            ".obj",
            ".ply",
            ".stl",
            ".vtp",
        }

    def load(self, path: StrPath) -> pv.PolyData:
        return load_poly_data(path)
