import abc
from typing import Any

import pyvista as pv

from liblaf import melon


class PreProcessAlgorithm(abc.ABC):
    data: pv.PolyData

    def __init__(self, data: Any) -> None:
        self.data = melon.as_poly_data(data)

    @abc.abstractmethod
    def run(self) -> pv.PolyData: ...
