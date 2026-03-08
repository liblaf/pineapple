from __future__ import annotations

import pathlib
from dataclasses import asdict, is_dataclass
from typing import Any

import anyio
import msgspec


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return _to_jsonable(value.model_dump())
    if hasattr(value, "dict") and callable(value.dict):
        return _to_jsonable(value.dict())
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    return value


def write_json_output_sync(folder: pathlib.Path, output: Any) -> None:
    encoded: bytes = msgspec.json.encode(_to_jsonable(output))
    (folder / "output.json").write_bytes(encoded)


def read_json_output_sync(folder: pathlib.Path) -> Any:
    data: bytes = (folder / "output.json").read_bytes()
    value: Any = msgspec.json.decode(data)
    return value


async def write_json_output_async(folder: anyio.Path, output: Any) -> None:
    encoded: bytes = msgspec.json.encode(_to_jsonable(output))
    await (folder / "output.json").write_bytes(encoded)


async def read_json_output_async(folder: anyio.Path) -> Any:
    data: bytes = await (folder / "output.json").read_bytes()
    value: Any = msgspec.json.decode(data)
    return value


__all__ = [
    "read_json_output_async",
    "read_json_output_sync",
    "write_json_output_async",
    "write_json_output_sync",
]
