from pathlib import Path

from liblaf import melon
from liblaf.melon.typed import StrPath


def load_dicom(path: StrPath) -> melon.DICOM:
    return melon.DICOM(path)


class DICOMReader(melon.io.AbstractReader):
    def match_path(self, path: StrPath) -> bool:
        path = Path(path)
        if path.is_dir() and (path / "DIRFILE").exists():
            return True
        if path.is_file() and path.name == "DIRFILE":  # noqa: SIM103
            return True
        return False

    def load(self, path: StrPath) -> melon.DICOM:
        return load_dicom(path)
