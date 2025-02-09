from pathlib import Path

from liblaf.melon.typed import StrPath


class UnsupportedReaderError(ValueError):
    path: Path

    def __init__(self, path: StrPath) -> None:
        self.path = Path(path)
        super().__init__(f"Cannot load `{self.path}`.")
