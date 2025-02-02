from typing import Any

from liblaf import melon
from liblaf.melon.typing import StrPath

from . import writer_dispatcher

writer_dispatcher.register(melon.io.pyvista.PolyDataWriter())


def save(path: StrPath, obj: Any) -> None:
    writer_dispatcher.save(path, obj)
