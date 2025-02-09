from pathlib import Path
from typing import Annotated

import numpy as np
import pyvista as pv
import typer
from jaxtyping import Float

import liblaf.grapes as grapes  # noqa: PLR0402
from liblaf import melon


def main(
    source_file: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    target_file: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    *,
    output_file: Annotated[Path, typer.Option("-o", "--output", dir_okay=False)],
) -> None:
    grapes.init_logging()
    source: pv.PolyData = melon.load_poly_data(source_file)
    target: pv.PolyData = melon.load_poly_data(target_file)
    source_landmarks: Float[np.ndarray, "N 3"] = melon.load_landmarks(source_file)
    target_landmarks: Float[np.ndarray, "N 3"] = melon.load_landmarks(target_file)
    transformed: pv.PolyData = melon.plugin.wrap.fast_wrapping(
        source=source,
        target=target,
        source_landmarks=source_landmarks,
        target_landmarks=target_landmarks,
    )
    melon.save(output_file, transformed)


if __name__ == "__main__":
    typer.run(main)
