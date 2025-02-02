from typing import Any

from liblaf import melon
from liblaf.melon.io import conversion_dispatcher


def as_dicom(obj: Any) -> melon.DICOM:
    return conversion_dispatcher.convert(obj, melon.DICOM)
