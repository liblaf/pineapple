import abc
from typing import Any

import pyvista as pv


class RegistrationAlgorithm(abc.ABC):
    def __init__(self, source: Any, target: Any) -> None:
        super().__init__()

    def preprocess_source(self) -> None:
        # 1. normalize source
        # 2. simplify source
        raise NotImplementedError

    def postprocess(self) -> pv.PointSet:
        # compute transformation matrix
        raise NotImplementedError
