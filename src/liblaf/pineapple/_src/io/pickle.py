from __future__ import annotations

import pathlib
import pickle
from typing import Any

import anyio


def write_pickle_output_sync(folder: pathlib.Path, output: Any) -> None:
    data: bytes = pickle.dumps(output, protocol=pickle.HIGHEST_PROTOCOL)
    (folder / "output.pkl").write_bytes(data)


def read_pickle_output_sync(folder: pathlib.Path) -> Any:
    data: bytes = (folder / "output.pkl").read_bytes()
    value: Any = pickle.loads(data)  # noqa: S301
    return value


async def write_pickle_output_async(folder: anyio.Path, output: Any) -> None:
    data: bytes = pickle.dumps(output, protocol=pickle.HIGHEST_PROTOCOL)
    await (folder / "output.pkl").write_bytes(data)


async def read_pickle_output_async(folder: anyio.Path) -> Any:
    data: bytes = await (folder / "output.pkl").read_bytes()
    value: Any = pickle.loads(data)  # noqa: S301
    return value


__all__ = [
    "read_pickle_output_async",
    "read_pickle_output_sync",
    "write_pickle_output_async",
    "write_pickle_output_sync",
]
