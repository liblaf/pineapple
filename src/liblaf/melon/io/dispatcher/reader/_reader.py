import abc
from pathlib import Path
from typing import Any

from liblaf.melon.typing import StrPath


class AbstractReader(abc.ABC):
    extension: str
    priority: int = 0

    @abc.abstractmethod
    def load(self, path: StrPath) -> Any: ...

    def match_path(self, path: StrPath) -> bool:
        path = Path(path)
        return path.suffix == self.extension
