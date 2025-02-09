import functools
from pathlib import Path
from typing import Self

import liblaf.grapes as grapes  # noqa: PLR0402
from liblaf import melon
from liblaf.melon.typed import StrPath

from . import Acquisition, Attachments, DICOMDatasetMeta, Subject, SubjectMeta


class DICOMDataset(Attachments):
    def __init__(self, path: StrPath, meta: DICOMDatasetMeta | None = None) -> None:
        super().__init__(path)
        if meta is not None:
            self.meta = meta
            self.save_meta()

    @property
    def acquisitions(self) -> list[Acquisition]:
        return [acq for subject in self.subjects for acq in subject.acquisitions]

    @functools.cached_property
    def meta(self) -> DICOMDatasetMeta:
        return grapes.load_pydantic(self.path / "dataset.json", DICOMDatasetMeta)

    @property
    def n_acquisitions(self) -> int:
        return sum(subject.n_acquisitions for subject in self.subjects)

    @property
    def n_subjects(self) -> int:
        return len(self.meta.subjects)

    @property
    def subjects(self) -> list[Subject]:
        return [Subject(self.path / subject_id) for subject_id in self.meta.subjects]

    def add_subject(self, meta: SubjectMeta) -> Subject:
        subject = Subject(self.path / meta.PatientID, meta)
        self.meta.subjects.append(subject.id)
        self.save_meta()
        return subject

    def clone(self, path: StrPath) -> Self:
        self.save_meta(path)
        return type(self)(path=path)

    def get_acquisition(
        self, subject_id: str, acq_date: melon.struct.dicom.DateLike
    ) -> Acquisition:
        subject: Subject = self.get_subject(subject_id)
        return subject.get_acquisition(acq_date)

    def get_subject(self, subject_id: str) -> Subject:
        return Subject(self.path / subject_id)

    def save_meta(self, path: StrPath | None = None) -> None:
        path = Path(path) if path else self.path
        path.mkdir(parents=True, exist_ok=True)
        grapes.save_pydantic(path / "dataset.json", self.meta)
        for subject in self.subjects:
            subject.save_meta(path / subject.id)
