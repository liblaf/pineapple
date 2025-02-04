from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
import pyvista as pv
from jaxtyping import ScalarLike

from liblaf import melon
from liblaf.melon.ops.transfer._utils import get_fill_value
from liblaf.melon.typing import Attrs

from . import TransferAlgorithm, TransferAlgorithmPrepared, TransferAuto


def transfer_point_to_point(
    source: Any,
    target: Any,
    data: Iterable[str],
    *,
    algo: TransferAlgorithm | None = None,
    fill_value: ScalarLike | Mapping[str, ScalarLike | None] | None = None,
) -> Attrs:
    if algo is None:
        algo = TransferAuto()
    if not isinstance(fill_value, Mapping):
        fill_value = {key: fill_value for key in data}
    prepared: TransferAlgorithmPrepared = algo.prepare(source, target)
    source: pv.PointSet = melon.as_point_set(source)
    result: Attrs = {}
    for key in data:
        attr: np.ndarray = source.point_data[key]
        fill: ScalarLike = get_fill_value(attr.dtype, fill_value.get(key))
        result[key] = prepared.transfer(attr, fill_value=fill)
    return result
