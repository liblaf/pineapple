from pathlib import Path
from typing import Any

from liblaf.melon.typing import StrPath


def save(path: StrPath, obj: Any) -> None:
    path = Path(path)
    raise NotImplementedError
