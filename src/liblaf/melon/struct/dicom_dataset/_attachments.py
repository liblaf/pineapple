from collections.abc import Mapping
from pathlib import Path
from typing import Any, Self

import pyvista as pv

from liblaf import melon
from liblaf.melon.typed import StrPath


class Attachments:
    path: Path

    def __init__(self, path: StrPath) -> None:
        self.path = Path(path)

    @classmethod
    def from_data(cls, path: StrPath, data: Mapping[str, Any]) -> Self:
        self: Self = cls(path)
        for key, value in data.items():
            self.save(key, value)
        return self

    def get(self, key: str) -> Path:
        return self.path / key

    def load(self, key: str) -> Any:
        return melon.load(self.get(key))

    def load_dicom(self, key: str) -> melon.DICOM:
        return melon.load_dicom(self.get(key))

    def load_poly_data(self, key: str) -> pv.PolyData:
        return melon.load_poly_data(self.get(key))

    def save(self, key: str, data: Any) -> None:
        melon.save(self.get(key), data)
