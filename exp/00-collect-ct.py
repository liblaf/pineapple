from pathlib import Path
from typing import Annotated

import typer
from loguru import logger

import liblaf.grapes as grapes  # noqa: PLR0402
import liblaf.melon as melon  # noqa: PLR0402


def find_subject(dataset: melon.DICOMDataset, dicom: melon.DICOM) -> melon.Subject:
    for subject in dataset.subjects:
        if (
            subject.patient_birth_date == dicom.patient_birth_date
            and subject.patient_name == dicom.patient_name
        ):
            if subject.patient_id != dicom.patient_id:
                logger.warning(
                    "Merge subjects: {} ({}) <- {}",
                    subject.patient_id,
                    subject.patient_name,
                    dicom.patient_id,
                )
            return subject
    logger.info("New subject: {} ({})", dicom.patient_id, dicom.patient_name)
    return dataset.add_subject(
        melon.SubjectMeta(
            PatientBirthDate=dicom.patient_birth_date,
            PatientID=dicom.patient_id,
            PatientName=dicom.patient_name,
            PatientSex=dicom.patient_sex,
        )
    )


def main(
    path: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
    *,
    output: Annotated[Path, typer.Option("-o", "--output", file_okay=False)] = Path(
        "data/00-raw/CT"
    ),
) -> None:
    grapes.init_logging()
    dirfile_paths: list[Path] = list(path.rglob("DIRFILE"))
    dataset = melon.DICOMDataset(output, meta=melon.DICOMDatasetMeta())
    for dirfile_path in grapes.track(dirfile_paths, description="Collect CT"):
        dicom: melon.DICOM = melon.load_dicom(dirfile_path)
        subject: melon.Subject = find_subject(dataset, dicom)
        acq: melon.Acquisition = subject.add_acquisition(
            melon.AcquisitionMeta(
                AcquisitionDate=dicom.acquisition_date,
                PatientAge=dicom.patient_age,
                PatientBirthDate=subject.patient_birth_date,
                PatientID=subject.patient_id,
                PatientName=subject.patient_name,
                PatientSex=subject.patient_sex,
            )
        )
        logger.info(
            "New acquisition: {} ({}) > {}",
            dicom.patient_id,
            dicom.patient_name,
            dicom.acquisition_date,
        )
        acq.save("CT/DIRFILE", dicom)


if __name__ == "__main__":
    typer.run(main)
