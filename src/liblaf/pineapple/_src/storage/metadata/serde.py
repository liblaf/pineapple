from __future__ import annotations

import os
import pathlib
from typing import Any, cast

import anyio

from liblaf.pineapple._src.storage.metadata.models import EntryMetadataModel


async def _run_sync(func: Any, *args: Any) -> None:
    run_sync: Any = cast("Any", anyio.to_thread).run_sync
    await run_sync(func, *args)


def write_metadata_atomic_sync(
    *,
    folder: pathlib.Path,
    key: str,
    user_metadata: dict[str, Any] | None,
) -> None:
    metadata = EntryMetadataModel.new(key=key, user=user_metadata)
    path = folder / "metadata.json"
    tmp_path = folder / "metadata.json.tmp"
    tmp_path.write_text(metadata.model_dump_json(indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


async def write_metadata_atomic_async(
    *,
    folder: anyio.Path,
    key: str,
    user_metadata: dict[str, Any] | None,
) -> None:
    metadata = EntryMetadataModel.new(key=key, user=user_metadata)
    path = folder / "metadata.json"
    tmp_path = folder / "metadata.json.tmp"
    await tmp_path.write_text(
        metadata.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    await _run_sync(os.replace, str(tmp_path), str(path))


__all__ = ["write_metadata_atomic_async", "write_metadata_atomic_sync"]
