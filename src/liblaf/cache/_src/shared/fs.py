from __future__ import annotations

import pathlib
import shutil


def directory_size_bytes(path: pathlib.Path) -> int:
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += child.stat().st_size
    return total


def safe_rmtree(path: pathlib.Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


__all__ = ["directory_size_bytes", "safe_rmtree"]
