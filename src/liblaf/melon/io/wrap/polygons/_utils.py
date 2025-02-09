from pathlib import Path

from liblaf import melon
from liblaf.melon.typed import StrPath


def get_polygons_path(path: StrPath) -> Path:
    path = Path(path)
    if path.suffix in melon.io.SUFFIXES:
        return path.with_suffix(".polygons.json")
    return path
