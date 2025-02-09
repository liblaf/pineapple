import bisect
from typing import Any

from liblaf.melon.typed import StrPath

from . import AbstractReader, UnsupportedReaderError


class ReaderDispatcher:
    readers: list[AbstractReader]

    def __init__(self) -> None:
        self.readers = []

    def register(self, reader: AbstractReader) -> None:
        bisect.insort(self.readers, reader, key=lambda r: r.priority)

    def load(self, path: StrPath) -> Any:
        for reader in self.readers:
            if reader.match_path(path):
                return reader.load(path)
        raise UnsupportedReaderError(path)


reader_dispatcher = ReaderDispatcher()
register_reader = reader_dispatcher.register
load = reader_dispatcher.load
