import datetime
import functools
from pathlib import Path
from typing import Literal, Self

import liblaf.grapes as grapes  # noqa: PLR0402
from liblaf import melon
from liblaf.melon.typed import StrPath

from . import Acquisition, AcquisitionMeta, Attachments, SubjectMeta


class Subject(Attachments):
    def __init__(self, path: StrPath, meta: SubjectMeta | None = None) -> None:
        super().__init__(path)
        if meta is not None:
            self.meta = meta
            self.save_meta()

    @property
    def acquisitions(self) -> list[Acquisition]:
        return [
            Acquisition(self.path / melon.struct.dicom.format_date(acq_date))
            for acq_date in self.meta.acquisitions
        ]

    @property
    def id(self) -> str:
        return self.patient_id

    @functools.cached_property
    def meta(self) -> SubjectMeta:
        return grapes.load_pydantic(self.path / "subject.json", SubjectMeta)

    @property
    def n_acquisitions(self) -> int:
        return len(self.meta.acquisitions)

    def add_acquisition(self, meta: AcquisitionMeta) -> Acquisition:
        acq_id: str = melon.struct.dicom.format_date(meta.AcquisitionDate)
        acq = Acquisition(self.path / acq_id, meta)
        self.meta.acquisitions.append(acq.acquisition_date)
        self.save_meta()
        return acq

    def clone(self, path: StrPath) -> Self:
        self.save_meta(path)
        return type(self)(path=path)

    def get_acquisition(self, acq_date: melon.struct.dicom.DateLike) -> Acquisition:
        acq_date: datetime.date = melon.struct.dicom.parse_date(acq_date)
        return Acquisition(self.path / melon.struct.dicom.format_date(acq_date))

    def save_meta(self, path: StrPath | None = None) -> None:
        path = Path(path) if path else self.path
        path.mkdir(parents=True, exist_ok=True)
        grapes.save_pydantic(path / "subject.json", self.meta)
        for acq in self.acquisitions:
            acq.save_meta(path / acq.id)

    # region metadata

    @property
    def patient_name(self) -> str:
        return self.meta.PatientName

    @property
    def patient_id(self) -> str:
        return self.meta.PatientID

    @property
    def patient_birth_date(self) -> datetime.date:
        return self.meta.PatientBirthDate

    @property
    def patient_sex(self) -> Literal["F", "M"]:
        return self.meta.PatientSex

    # endregion metadata
