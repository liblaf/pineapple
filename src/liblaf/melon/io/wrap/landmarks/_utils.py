from pathlib import Path

from liblaf import melon
from liblaf.melon.typed import StrPath


def get_landmarks_path(path: StrPath) -> Path:
    path = Path(path)
    if path.suffix in melon.io.SUFFIXES:
        return path.with_suffix(".landmarks.json")
    return path
