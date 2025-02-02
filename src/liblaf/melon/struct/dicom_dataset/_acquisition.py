import functools
from pathlib import Path

from liblaf import grapes
from liblaf.melon.typing import StrPath

from . import AcquisitionMeta


class Acquisition:
    path: Path

    def __init__(self, path: StrPath) -> None:
        self.path = Path(path)

    @property
    def attachments(self) -> list[str]:
        return self.meta.attachments

    @functools.cached_property
    def meta(self) -> AcquisitionMeta:
        raise NotImplementedError

    def save(self, path: StrPath) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        grapes.save_pydantic(path / "acquisition.json", self.meta)
