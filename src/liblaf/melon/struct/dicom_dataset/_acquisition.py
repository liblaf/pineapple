import datetime
import functools
from pathlib import Path
from typing import Self

# make pyright happy
import liblaf.grapes as grapes  # noqa: PLR0402
from liblaf import melon
from liblaf.melon.typing import StrPath

from . import AcquisitionMeta, Attachments


class Acquisition:
    path: Path

    def __init__(
        self,
        path: StrPath | None = None,
        attachments: Attachments | None = None,
        meta: AcquisitionMeta | None = None,
    ) -> None:
        self.path = Path(path or ".")
        if attachments is not None:
            self.attachments = attachments
        if meta is not None:
            self.meta = meta

    @classmethod
    def from_dicom(cls, dicom: melon.DICOM) -> Self:
        return cls(
            attachments=Attachments.from_data(data={"CT/DIRFILE": dicom}),
            meta=AcquisitionMeta(
                AcquisitionDate=dicom.acquisition_date,
                PatientAge=dicom.patient_age,
                PatientBirthDate=dicom.patient_birth_date,
                PatientID=dicom.patient_id,
                PatientName=dicom.patient_name,
                PatientSex=dicom.patient_sex,
            ),
        )

    @functools.cached_property
    def attachments(self) -> Attachments:
        return Attachments(root=self.path, keys=self.meta.attachments)

    @functools.cached_property
    def meta(self) -> AcquisitionMeta:
        return grapes.load_pydantic(self.path / "acquisition.json", AcquisitionMeta)

    def save(self, path: StrPath) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        self.meta.attachments = self.attachments.meta
        grapes.save_pydantic(path / "acquisition.json", self.meta)
        self.attachments.save(path)

    @property
    def acquisition_date(self) -> datetime.date:
        return self.meta.AcquisitionDate

    @property
    def acquisition_date_str(self) -> str:
        return melon.struct.dicom.format_date(self.acquisition_date)
