from pathlib import Path
from typing import Any

import pyvista as pv

from liblaf import melon
from liblaf.melon.typing import StrPath

from . import as_poly_data


class PolyDataWriter(melon.io.AbstractWriter):
    def match_path(self, path: StrPath) -> bool:
        path = Path(path)
        return path.suffix in {
            ".obj",
            ".ply",
            ".stl",
            ".vtp",
        }

    def save(self, path: StrPath, obj: Any) -> None:
        path = Path(path)
        obj: pv.PolyData = as_poly_data(obj)
        path.parent.mkdir(parents=True, exist_ok=True)
        obj.save(path)
