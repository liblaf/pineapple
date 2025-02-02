from typing import Any

import pyvista as pv
from loguru import logger


class UnsupportedConversionError(TypeError):
    obj: Any
    type_to: type

    def __init__(self, obj: Any, type_to: type) -> None:
        self.obj = obj
        self.type_to = type_to
        super().__init__(f"Cannot convert `{obj}` to `{type_to}`.")


def warning_unsupported_association(
    to: type, association: pv.FieldAssociation, attr: Any | None = None
) -> None:
    if attr is None:
        return
    logger.warning("{:r} does not support {:r} data", to, association)
