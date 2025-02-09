from pathlib import Path

from liblaf.melon.typed import StrPath


def match_path(path: StrPath) -> bool:
    path = Path(path)
    return path.suffix in {".obj", ".stl", ".vtp", ".ply"}
