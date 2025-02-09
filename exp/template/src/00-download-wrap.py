import shutil
from pathlib import Path
from typing import Annotated

import typer

import liblaf.grapes as grapes  # noqa: PLR0402


def main(
    gallery_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)] = Path(  # noqa: B008
        "~/.local/opt/Wrap/Gallery"
    ).expanduser(),
    *,
    output: Annotated[Path, typer.Option("-o", "--output", file_okay=False)] = Path(
        "data/template/00-raw/wrap"
    ),
) -> None:
    grapes.init_logging()
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(gallery_dir / "Basemeshes/WrapSkull.obj", output / "cranium.obj")
    shutil.copy2(gallery_dir / "Basemeshes/WrapJaw.obj", output / "mandible.obj")
    shutil.copy2(
        gallery_dir / "TexturingXYZ/XYZ_ReadyToSculpt_eyesOpen_PolyGroups_GEO.obj",
        output / "face.obj",
    )


if __name__ == "__main__":
    typer.run(main)
