import shutil
from pathlib import Path
from typing import Annotated

import typer

import liblaf.grapes as grapes  # noqa: PLR0402


def main(
    gallery_dir: Annotated[
        Path | None, typer.Argument(exists=True, file_okay=False)
    ] = None,
    *,
    output: Annotated[
        Path | None, typer.Option("-o", "--output", file_okay=False)
    ] = None,
) -> None:
    grapes.init_logging()
    if gallery_dir is None:
        gallery_dir = Path("~/.local/opt/Wrap/Gallery").expanduser()
    if output is None:
        output = grapes.git.root_safe() / "data/template/wrap/00-raw/wrap"
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(gallery_dir / "Basemeshes/WrapSkull.obj", output / "cranium.obj")
    shutil.copy2(gallery_dir / "Basemeshes/WrapJaw.obj", output / "mandible.obj")
    shutil.copy2(
        gallery_dir / "TexturingXYZ/XYZ_ReadyToSculpt_eyesOpen_PolyGroups_GEO.obj",
        output / "face.obj",
    )


if __name__ == "__main__":
    typer.run(main)
