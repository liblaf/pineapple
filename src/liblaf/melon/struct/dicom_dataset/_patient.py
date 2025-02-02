import functools
from collections.abc import Iterable
from pathlib import Path
from typing import Self

# make pyright happy
import liblaf.grapes as grapes  # noqa: PLR0402
from liblaf import melon
from liblaf.melon.typing import StrPath

from . import Acquisition, Attachments, PatientMeta


class Patient:
    path: Path

    def __init__(
        self,
        path: StrPath | None = None,
        acquisitions: Iterable[Acquisition] | None = None,
        attachments: Attachments | None = None,
        meta: PatientMeta | None = None,
    ) -> None:
        self.path = Path(path or ".")
        if acquisitions is not None:
            self.acquisitions = list(acquisitions)
        if attachments is not None:
            self.attachments = attachments
        if meta is not None:
            self.meta = meta

    @classmethod
    def from_acquisitions(cls, acquisitions: Iterable[Acquisition]) -> Self:
        first: Acquisition = next(iter(acquisitions))
        return cls(
            acquisitions=acquisitions,
            meta=PatientMeta(
                acquisitions=[acq.meta for acq in acquisitions],
                PatientAge=first.meta.PatientAge,
                PatientBirthDate=first.meta.PatientBirthDate,
                PatientID=first.meta.PatientID,
                PatientName=first.meta.PatientName,
                PatientSex=first.meta.PatientSex,
            ),
        )

    @functools.cached_property
    def acquisitions(self) -> list[Acquisition]:
        return [
            Acquisition(
                self.path / melon.struct.dicom.format_date(acq_meta.AcquisitionDate)
            )
            for acq_meta in self.meta.acquisitions
        ]

    @functools.cached_property
    def attachments(self) -> Attachments:
        return Attachments(root=self.path, keys=self.meta.attachments)

    @functools.cached_property
    def meta(self) -> PatientMeta:
        return grapes.load_pydantic(self.path / "patient.json", PatientMeta)

    def save(self, path: StrPath) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        self.meta.attachments = self.attachments.meta
        self.meta.acquisitions = [acq.meta for acq in self.acquisitions]
        grapes.save_pydantic(path / "patient.json", self.meta)
        self.attachments.save(path)
        for acq in self.acquisitions:
            acq.save(path / acq.acquisition_date_str)

    @property
    def patient_id(self) -> str:
        return self.meta.PatientID
