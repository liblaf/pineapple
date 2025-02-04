from typing import Any, Protocol

import numpy as np
from jaxtyping import ScalarLike, Shaped
from numpy.typing import ArrayLike


class TransferAlgorithmPrepared(Protocol):
    def transfer(
        self, data: Shaped[ArrayLike, "source_points ..."], fill_value: ScalarLike
    ) -> Shaped[np.ndarray, "target_points ..."]: ...


class TransferAlgorithm(Protocol):
    def prepare(self, source: Any, target: Any) -> TransferAlgorithmPrepared: ...
