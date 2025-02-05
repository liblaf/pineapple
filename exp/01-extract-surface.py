from pathlib import Path
from typing import Annotated

import pyvista as pv
import typer
from loguru import logger

import liblaf.grapes as grapes  # noqa: PLR0402
import liblaf.melon as melon  # noqa: PLR0402


def main(
    dataset: Annotated[Path, typer.Option(exists=True, file_okay=False)] = Path(
        "data/00-raw/CT/"
    ),
    *,
    output: Annotated[Path, typer.Option("-o", "--output", file_okay=False)] = Path(
        "data/00-raw/surface/"
    ),
) -> None:
    grapes.init_logging()
    inputs = melon.DICOMDataset(dataset)
    outputs: melon.DICOMDataset = inputs.clone(output)
    for in_acq in grapes.track(inputs.acquisitions, description="Extract Surface"):
        logger.info(
            "Acquisition: {} ({}) > {}",
            in_acq.patient_id,
            in_acq.patient_name,
            in_acq.acquisition_date,
        )
        out_acq: melon.Acquisition = outputs.get_acquisition(
            in_acq.patient_id, in_acq.acquisition_date
        )
        dicom: melon.DICOM = in_acq.load_dicom("CT/DIRFILE")
        ct: pv.ImageData = dicom.image_data
        ct = ct.gaussian_smooth()  # pyright: ignore[reportAssignmentType]
        face: pv.PolyData = ct.contour([-200.0])  # pyright: ignore[reportArgumentType, reportAssignmentType]
        face.connectivity("largest", inplace=True)
        out_acq.save("face.ply", face)
        skull: pv.PolyData = ct.contour([200.0])  # pyright: ignore[reportArgumentType, reportAssignmentType]
        skull.connectivity("largest", inplace=True)
        out_acq.save("skull.ply", skull)


if __name__ == "__main__":
    typer.run(main)
