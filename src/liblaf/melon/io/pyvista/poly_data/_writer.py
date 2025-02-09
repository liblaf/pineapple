from pathlib import Path
from typing import Any

import pyvista as pv

from liblaf import melon
from liblaf.melon.typed import StrPath

from . import as_poly_data, match_path, save_obj


class PolyDataWriter(melon.io.AbstractWriter):
    def match_path(self, path: StrPath) -> bool:
        return match_path(path)

    def save(self, path: StrPath, obj: Any) -> None:
        path = Path(path)
        obj: pv.PolyData = as_poly_data(obj)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".obj":
            save_obj(path, obj)
        else:
            obj.save(path)
