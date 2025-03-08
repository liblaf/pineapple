from pathlib import Path
from typing import Annotated

import numpy as np
import pooch
import pyvista as pv
import typer
from numpy.typing import ArrayLike

import liblaf.grapes as grapes  # noqa: PLR0402
import liblaf.melon as melon  # noqa: PLR0402


def main(
    *,
    output: Annotated[
        Path | None, typer.Option("-o", "--output", file_okay=False)
    ] = None,
) -> None:
    grapes.init_logging()
    if output is None:
        output = grapes.git.root_safe() / "data/template/wrap/00-raw/sculptor"
    paradict_path = Path(
        pooch.retrieve(
            url="https://raw.githubusercontent.com/sculptor2022/sculptor/refs/heads/main/model/paradict.npy",
            known_hash="sha256:43b0773ef04c20afd12789d68c492115d6ffe11038d600eb9b989a4af4c91f00",
            progressbar=True,
        )
    )
    paradict: dict[str, ArrayLike] = np.load(paradict_path, allow_pickle=True).item()
    face: pv.PolyData = melon.as_poly_data(
        {"points": paradict["template_face"], "cells": paradict["facialmesh_face"]}
    )
    melon.save(output / "face.obj", face)
    melon.save(output / "face.ply", face)
    skull: pv.PolyData = melon.as_poly_data(
        {"points": paradict["template_skull"], "cells": paradict["skullmesh_face"]}
    )
    melon.save(output / "skull.obj", skull)
    melon.save(output / "skull.ply", skull)
    bodies: pv.MultiBlock = skull.split_bodies().as_polydata_blocks()
    cranium: pv.PolyData
    mandible: pv.PolyData
    cranium, mandible = bodies  # pyright: ignore[reportAssignmentType]
    melon.save(output / "cranium.obj", cranium)
    melon.save(output / "cranium.ply", cranium)
    melon.save(output / "mandible.obj", mandible)
    melon.save(output / "mandible.ply", mandible)


if __name__ == "__main__":
    typer.run(main)
