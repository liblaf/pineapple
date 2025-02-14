import abc
from collections.abc import Container
from pathlib import Path
from typing import Any

from liblaf.melon.typed import StrPath


class AbstractWriter(abc.ABC):
    extensions: Container[str]
    priority: int = 0

    @abc.abstractmethod
    def save(self, path: StrPath, obj: Any) -> None: ...

    def match_path(self, path: StrPath) -> bool:
        path = Path(path)
        return path.suffix in self.extensions
