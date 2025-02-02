import functools
from collections.abc import Iterable
from pathlib import Path
from typing import Self

import liblaf.grapes as grapes  # noqa: PLR0402
from liblaf.melon.struct.dicom_dataset._patient import Patient
from liblaf.melon.typing import StrPath

from . import Attachments, DICOMDatasetMeta


class DICOMDataset:
    path: Path

    def __init__(
        self,
        path: StrPath | None = None,
        attachments: Attachments | None = None,
        meta: DICOMDatasetMeta | None = None,
        patients: Iterable[Patient] | None = None,
    ) -> None:
        self.path = Path(path or ".")
        if attachments is not None:
            self.attachments = attachments
        if meta is not None:
            self.meta = meta
        if patients is not None:
            self.patients = {patient.patient_id: patient for patient in patients}

    @classmethod
    def from_patients(cls, patients: Iterable[Patient]) -> Self:
        return cls(
            patients=patients,
            meta=DICOMDatasetMeta(
                patients={patient.patient_id: patient.meta for patient in patients}
            ),
        )

    @functools.cached_property
    def attachments(self) -> Attachments:
        return Attachments(root=self.path, keys=self.meta.attachments)

    @functools.cached_property
    def meta(self) -> DICOMDatasetMeta:
        return grapes.load_pydantic(self.path / "dataset.json", DICOMDatasetMeta)

    @functools.cached_property
    def patients(self) -> dict[str, Patient]:
        return {
            patient_id: Patient(self.path / patient_id)
            for patient_id, patient_meta in self.meta.patients.items()
        }

    def save(self, path: StrPath) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        self.meta.attachments = self.attachments.meta
        self.meta.patients = {
            patient_id: patient.meta for patient_id, patient in self.patients.items()
        }
        grapes.save_pydantic(path / "dataset.json", self.meta)
        for patient in self.patients.values():
            patient.save(path / patient.meta.PatientID)
