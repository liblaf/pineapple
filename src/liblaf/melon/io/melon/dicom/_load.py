from liblaf import melon
from liblaf.melon.typing import StrPath


def load_dicom(path: StrPath) -> melon.DICOM:
    return melon.DICOM(path)
