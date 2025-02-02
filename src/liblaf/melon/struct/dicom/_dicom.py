import datetime
import functools
import shutil
from pathlib import Path
from typing import Literal

import pydicom
import pydicom.valuerep
import pyvista as pv

from liblaf import melon
from liblaf.melon.typing import StrPath

from . import DICOMMeta


class DICOM:
    path: Path

    def __init__(self, path: StrPath) -> None:
        path = Path(path)
        if path.is_file() and path.name == "DIRFILE":
            path = path.parent
        self.path = path

    @functools.cached_property
    def dirfile_path(self) -> Path:
        return self.path / "DIRFILE"

    @functools.cached_property
    def dirfile(self) -> pydicom.FileDataset:
        return pydicom.dcmread(self.dirfile_path)

    @functools.cached_property
    def first_record(self) -> pydicom.FileDataset:
        return pydicom.dcmread(self.record_filepaths[0])

    @functools.cached_property
    def image_data(self) -> pv.ImageData:
        return melon.load_image_data(self.path)

    @functools.cached_property
    def meta(self) -> DICOMMeta:
        return DICOMMeta(
            AcquisitionDate=self.acquisition_date,
            PatientAge=self.patient_age,
            PatientBirthDate=self.patient_birth_date,
            PatientID=self.patient_id,
            PatientName=self.patient_name,
            PatientSex=self.patient_sex,
        )

    @functools.cached_property
    def record_filepaths(self) -> list[Path]:
        directory_record_sequence: pydicom.Sequence = self.dirfile[
            "DirectoryRecordSequence"
        ].value
        return [
            self.path / record["ReferencedFileID"][-1]
            for record in directory_record_sequence
        ]

    def save(self, path: StrPath) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.dirfile_path, path / "DIRFILE")
        for record_filepath in self.record_filepaths:
            shutil.copy2(record_filepath, path / record_filepath.name)

    # region metadata
    @functools.cached_property
    def acquisition_date(self) -> datetime.date:
        return datetime.datetime.strptime(  # noqa: DTZ007
            self.first_record["AcquisitionDate"].value, "%Y%m%d"
        ).date()

    @functools.cached_property
    def patient_name(self) -> str:
        name: pydicom.valuerep.PersonName = self.first_record["PatientName"].value
        return str(name)

    @functools.cached_property
    def patient_id(self) -> str:
        return self.first_record["PatientID"].value

    @functools.cached_property
    def patient_birth_date(self) -> datetime.date:
        return datetime.datetime.strptime(  # noqa: DTZ007
            self.first_record["PatientBirthDate"].value, "%Y%m%d"
        ).date()

    @functools.cached_property
    def patient_sex(self) -> Literal["F", "M"]:
        return self.first_record["PatientSex"].value

    @functools.cached_property
    def patient_age(self) -> int:
        age_str: str = self.first_record["PatientAge"].value
        return int(age_str.removesuffix("Y"))

    # endregion metadata
