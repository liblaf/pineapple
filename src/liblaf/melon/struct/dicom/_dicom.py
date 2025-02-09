import datetime
import shutil
from pathlib import Path
from typing import Literal

import pydicom
import pydicom.valuerep
import pyvista as pv

from liblaf import melon
from liblaf.melon.typed import StrPath

from . import DICOMMeta, dcmread_cached, parse_date


class DICOM:
    path: Path

    def __init__(self, path: StrPath) -> None:
        path = Path(path)
        if path.name == "DIRFILE":
            path = path.parent
        self.path = path

    @property
    def dirfile_path(self) -> Path:
        return self.path / "DIRFILE"

    @property
    def dirfile(self) -> pydicom.FileDataset:
        return dcmread_cached(self.dirfile_path)

    @property
    def first_record(self) -> pydicom.FileDataset:
        return dcmread_cached(self.record_filepaths[0])

    @property
    def image_data(self) -> pv.ImageData:
        return melon.load_image_data(self.path)

    @property
    def meta(self) -> DICOMMeta:
        return DICOMMeta(
            AcquisitionDate=self.acquisition_date,
            PatientAge=self.patient_age,
            PatientBirthDate=self.patient_birth_date,
            PatientID=self.patient_id,
            PatientName=self.patient_name,
            PatientSex=self.patient_sex,
        )

    @property
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
        if path.name == "DIRFILE":
            path = path.parent
        path.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.dirfile_path, path / "DIRFILE")
        for record_filepath in self.record_filepaths:
            shutil.copy2(record_filepath, path / record_filepath.name)

    # region metadata
    @property
    def acquisition_date(self) -> datetime.date:
        return parse_date(self.first_record["AcquisitionDate"].value)

    @property
    def patient_name(self) -> str:
        name: pydicom.valuerep.PersonName = self.first_record["PatientName"].value
        return str(name)

    @property
    def patient_id(self) -> str:
        return self.first_record["PatientID"].value

    @property
    def patient_birth_date(self) -> datetime.date:
        return parse_date(self.first_record["PatientBirthDate"].value)

    @property
    def patient_sex(self) -> Literal["F", "M"]:
        return self.first_record["PatientSex"].value

    @property
    def patient_age(self) -> int:
        age_str: str = self.first_record["PatientAge"].value
        return int(age_str.removesuffix("Y"))

    # endregion metadata
