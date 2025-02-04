import attrs
import numpy as np
from jaxtyping import ScalarLike, Shaped
from numpy.typing import ArrayLike

from . import NearestInterpolatedAuxiliary, TransferNearestInterpolated


@attrs.define(frozen=True)
class TransferAuto(TransferNearestInterpolated):
    def transfer(
        self,
        aux: NearestInterpolatedAuxiliary,
        data: Shaped[ArrayLike, " source_points *shape"],
        fill_value: ScalarLike | None = None,
    ) -> Shaped[np.ndarray, " target_points *shape"]:
        data: Shaped[ArrayLike, " source_points *shape"] = np.asarray(data)
        if np.isdtype(data.dtype, ("bool", "integer")):
            return aux.nearest_vertex.transfer(aux.nearest_vertex_aux, data, fill_value)
        return super().transfer(aux, data, fill_value)
