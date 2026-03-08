from __future__ import annotations

import pathlib
from typing import Any

import anyio


def write_repr_inputs_sync(folder: pathlib.Path, *args: Any, **kwargs: Any) -> None:
    payload: str = repr({"args": args, "kwargs": kwargs})
    (folder / "inputs.txt").write_text(payload + "\n", encoding="utf-8")


async def write_repr_inputs_async(
    folder: anyio.Path, *args: Any, **kwargs: Any
) -> None:
    payload: str = repr({"args": args, "kwargs": kwargs})
    await (folder / "inputs.txt").write_text(payload + "\n", encoding="utf-8")


__all__ = ["write_repr_inputs_async", "write_repr_inputs_sync"]
