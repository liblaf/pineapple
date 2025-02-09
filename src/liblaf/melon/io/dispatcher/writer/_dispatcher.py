import bisect
from typing import Any

from liblaf.melon.typed import StrPath

from . import AbstractWriter, UnsupportedWriterError


class WriterDispatcher:
    writers: list[AbstractWriter]

    def __init__(self) -> None:
        self.writers = []

    def register(self, writer: AbstractWriter) -> None:
        bisect.insort(self.writers, writer, key=lambda r: r.priority)

    def save(self, path: StrPath, obj: Any) -> None:
        for writer in self.writers:
            if writer.match_path(path):
                return writer.save(path, obj)
        raise UnsupportedWriterError(path)


writer_dispatcher = WriterDispatcher()
register_writer = writer_dispatcher.register
save = writer_dispatcher.save
