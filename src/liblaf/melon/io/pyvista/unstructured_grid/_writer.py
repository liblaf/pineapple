from collections.abc import Container
from pathlib import Path
from typing import Any

import pyvista as pv

from liblaf import melon
from liblaf.melon.typed import StrPath

from . import as_unstructured_grid


class UnstructuredGridWriter(melon.io.AbstractWriter):
    extensions: Container[str] = {"*.vtu"}

    def save(self, path: StrPath, obj: Any) -> None:
        path = Path(path)
        obj: pv.UnstructuredGrid = as_unstructured_grid(obj)
        path.parent.mkdir(parents=True, exist_ok=True)
        obj.save(path)
