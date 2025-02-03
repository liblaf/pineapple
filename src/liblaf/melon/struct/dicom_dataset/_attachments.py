from collections.abc import Mapping
from pathlib import Path
from typing import Any, Self

from liblaf import melon
from liblaf.melon.typing import StrPath


class Attachments:
    root: Path

    def __init__(self, root: StrPath) -> None:
        self.root = Path(root)

    @classmethod
    def from_data(cls, path: StrPath, data: Mapping[str, Any]) -> Self:
        self: Self = cls(path)
        for key, value in data.items():
            self.save(key, value)
        return self

    def get(self, key: str) -> Path:
        return self.root / key

    def load(self, key: str) -> Any:
        return melon.load(self.get(key))

    def save(self, key: str, value: Any) -> None:
        melon.save(self.get(key), value)
