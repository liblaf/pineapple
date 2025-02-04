from typing import Any

import attrs
import numpy as np
from jaxtyping import ScalarLike, Shaped
from numpy.typing import ArrayLike

from . import (
    TransferAlgorithm,
    TransferAlgorithmPrepared,
    TransferNearestPointOnSurface,
    TransferNearestVertex,
)


@attrs.frozen
class TransferAutoPrepared(TransferAlgorithmPrepared):
    categorial: TransferAlgorithmPrepared
    floating: TransferAlgorithmPrepared

    def transfer(
        self, data: Shaped[ArrayLike, "source_points ..."], fill_value: ScalarLike
    ) -> Shaped[np.ndarray, "target_points ..."]:
        data: Shaped[np.ndarray, "source_points ..."] = np.asarray(data)
        if np.isdtype(data.dtype, ("bool", "integer")):
            return self.categorial.transfer(data, fill_value)
        return self.floating.transfer(data, fill_value)


@attrs.frozen
class TransferAuto(TransferAlgorithm):
    categorial: TransferAlgorithm = attrs.field(factory=TransferNearestVertex)
    floating: TransferAlgorithm = attrs.field(factory=TransferNearestPointOnSurface)

    def prepare(self, source: Any, target: Any) -> TransferAutoPrepared:
        return TransferAutoPrepared(
            floating=self.floating.prepare(source, target),
            categorial=self.categorial.prepare(source, target),
        )
