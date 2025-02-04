from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
import pyvista as pv
from jaxtyping import ScalarLike

from liblaf import melon
from liblaf.melon.typing import Attrs

from . import TransferAlgorithm, TransferAuto


def transfer_point_to_point(
    source: Any,
    target: Any,
    data: Iterable[str],
    *,
    algorithm: TransferAlgorithm | None = None,
    fill_value: ScalarLike | Mapping[str, ScalarLike | None] | None = None,
) -> Attrs:
    if algorithm is None:
        algorithm = TransferAuto()
    if not isinstance(fill_value, Mapping):
        fill_value = {attr: fill_value for attr in data}
    aux: Any = algorithm.prepare(source, target)
    source: pv.PointSet = melon.as_point_set(source)
    target: pv.PointSet = melon.as_point_set(target)
    result: Attrs = {
        attr: algorithm.transfer(
            aux, source.point_data[attr], fill_value=fill_value[attr]
        )
        for attr in data
    }
    for attr in data:
        fill: ScalarLike | None = fill_value.get(attr)
        if fill is None:
            fill = np.zeros((), dtype=result[attr].dtype).item()
        result[attr] = algorithm.transfer(aux, source.point_data[attr], fill_value=fill)
    return result
