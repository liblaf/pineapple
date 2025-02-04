from typing import Any

import trimesh as tm

from liblaf.melon.io import conversion_dispatcher

from . import PolyDataToTrimesh

conversion_dispatcher.register(PolyDataToTrimesh())


def as_trimesh(data: Any) -> tm.Trimesh:
    return conversion_dispatcher.convert(data, tm.Trimesh)
