import datetime
import functools
from pathlib import Path
from typing import Literal, Self

# make pyright happy
import liblaf.grapes as grapes  # noqa: PLR0402
from liblaf import melon
from liblaf.melon.typed import StrPath

from . import AcquisitionMeta, Attachments


class Acquisition(Attachments):
    def __init__(self, path: StrPath, meta: AcquisitionMeta | None = None) -> None:
        super().__init__(path)
        if meta is not None:
            self.meta = meta
            self.save_meta()

    @property
    def id(self) -> str:
        return melon.struct.dicom.format_date(self.acquisition_date)

    @functools.cached_property
    def meta(self) -> AcquisitionMeta:
        return grapes.load_pydantic(self.path / "acquisition.json", AcquisitionMeta)

    @property
    def subject_id(self) -> str:
        return self.meta.PatientID

    def clone(self, path: StrPath) -> Self:
        self.save_meta(path)
        return type(self)(path=path, meta=self.meta)

    def save_meta(self, path: StrPath | None = None) -> None:
        path = Path(path) if path else self.path
        path.mkdir(parents=True, exist_ok=True)
        grapes.save_pydantic(path / "acquisition.json", self.meta)

    # region metadata

    @property
    def acquisition_date(self) -> datetime.date:
        return self.meta.AcquisitionDate

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

    @property
    def patient_age(self) -> int:
        return self.meta.PatientAge

    # endregion metadata
