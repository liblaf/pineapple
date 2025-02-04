import abc
from typing import Any

import pyvista as pv

from liblaf import melon


class RigidRegistrationAlgorithm(abc.ABC):
    source: pv.PolyData
    target: pv.PolyData
    normalize_source: bool = True
    normalize_target: bool = True
    sample_source: bool = True
    sample_target: bool = True
    simplify_source: bool = True
    simplify_target: bool = True

    def __init__(
        self,
        source: Any,
        target: Any,
        *,
        normalize_source: bool = True,
        sample_source: bool = True,
        simplify_source: bool = True,
    ) -> None:
        self.source = melon.as_poly_data(source)
        self.target = melon.as_poly_data(target)
        self.normalize_source = normalize_source

    def preprocess_source(self) -> None:
        if self.normalize_source:
            raise NotImplementedError
        raise NotImplementedError
