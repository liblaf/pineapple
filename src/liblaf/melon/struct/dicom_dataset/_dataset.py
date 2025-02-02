from collections.abc import Mapping
from typing import Any


class DICOMDataset(Mapping[str, Any]):
    def __init__(self) -> None:
        raise NotImplementedError
