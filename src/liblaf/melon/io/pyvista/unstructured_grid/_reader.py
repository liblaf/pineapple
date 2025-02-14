from collections.abc import Container
from pathlib import Path

import pyvista as pv

from liblaf import melon
from liblaf.melon.typed import StrPath


def load_unstructured_grid(path: StrPath) -> pv.UnstructuredGrid:
    path = Path(path)
    return pv.read(path)  # pyright: ignore[reportReturnType]


class UnstructuredGridReader(melon.io.AbstractReader):
    extensions: Container[str] = {".vtu"}

    def load(self, path: StrPath) -> pv.UnstructuredGrid:
        return load_unstructured_grid(path)
