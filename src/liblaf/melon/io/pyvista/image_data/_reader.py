from pathlib import Path

import pyvista as pv

from liblaf.melon.typed import StrPath


def load_image_data(path: StrPath) -> pv.ImageData:
    path = Path(path)
    if path.is_file() and path.name == "DIRFILE":
        path = path.parent
    if path.is_dir() and (path / "DIRFILE").exists():
        return pv.read(path, force_ext=".dcm")  # pyright: ignore[reportReturnType]
    return pv.read(path)  # pyright: ignore[reportReturnType]
