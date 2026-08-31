from __future__ import annotations

import importlib
import pathlib
import pprint
from typing import Any

import anyio


def _format_inputs(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    value = {"args": args, "kwargs": kwargs}
    try:
        liblaf_pprint: Any = importlib.import_module("liblaf.pprint")
    except ModuleNotFoundError as error:  # pragma: no cover - optional sibling adapter
        if error.name != "liblaf.pprint":
            raise
        return pprint.pformat(value)
    return str(liblaf_pprint.pformat(value))


def write_repr_inputs_sync(folder: pathlib.Path, *args: Any, **kwargs: Any) -> None:
    payload = _format_inputs(args, kwargs)
    (folder / "inputs.txt").write_text(payload + "\n", encoding="utf-8")


async def write_repr_inputs_async(
    folder: anyio.Path, *args: Any, **kwargs: Any
) -> None:
    payload = _format_inputs(args, kwargs)
    await (folder / "inputs.txt").write_text(payload + "\n", encoding="utf-8")


__all__ = ["write_repr_inputs_async", "write_repr_inputs_sync"]
