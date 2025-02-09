from pathlib import Path
from typing import Any

from liblaf import melon
from liblaf.melon.typed import StrPath

from . import as_dicom


class DICOMWriter(melon.io.AbstractWriter):
    def match_path(self, path: StrPath) -> bool:
        path = Path(path)
        if path.name == "DIRFILE":  # noqa: SIM103
            return True
        return False

    def save(self, path: StrPath, obj: Any) -> None:
        obj: melon.DICOM = as_dicom(obj)
        obj.save(path)
