from pathlib import Path

from liblaf.melon.typed import StrPath


class UnsupportedWriterError(ValueError):
    path: Path

    def __init__(self, path: StrPath) -> None:
        self.path = Path(path)
        super().__init__(f"Cannot save `{self.path}`.")
