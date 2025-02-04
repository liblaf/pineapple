from typing import Any, Protocol, TypeVar

import numpy as np
from jaxtyping import ScalarLike, Shaped
from numpy.typing import ArrayLike

_T = TypeVar("_T")


class TransferAlgorithm(Protocol[_T]):
    def prepare(self, source: Any, target: Any) -> _T: ...
    def transfer(
        self,
        aux: _T,
        data: Shaped[ArrayLike, " source_points *shape"],
        fill_value: ScalarLike | None = None,
    ) -> Shaped[np.ndarray, " target_points *shape"]: ...
