from __future__ import annotations

import importlib
import io
import pathlib
from typing import Any

import anyio


def _load_numpy() -> Any | None:
    module: Any | None
    try:
        module = importlib.import_module("numpy")
    except ModuleNotFoundError:  # pragma: no cover - optional dependency
        return None
    return module


def require_numpy() -> Any:
    module: Any | None = _load_numpy()
    if module is None:
        msg: str = "numpy is required for numpy output reader/writer"
        raise ModuleNotFoundError(msg)
    return module


def write_numpy_output_sync(folder: pathlib.Path, output: Any) -> None:
    np: Any = require_numpy()
    np.save(folder / "output.npy", output)


def read_numpy_output_sync(folder: pathlib.Path) -> Any:
    np: Any = require_numpy()
    value: Any = np.load(folder / "output.npy", allow_pickle=True)
    return value


async def write_numpy_output_async(folder: anyio.Path, output: Any) -> None:
    np: Any = require_numpy()
    buffer: io.BytesIO = io.BytesIO()
    np.save(buffer, output)
    await (folder / "output.npy").write_bytes(buffer.getvalue())


async def read_numpy_output_async(folder: anyio.Path) -> Any:
    np: Any = require_numpy()
    data: bytes = await (folder / "output.npy").read_bytes()
    value: Any = np.load(io.BytesIO(data), allow_pickle=True)
    return value


__all__ = [
    "read_numpy_output_async",
    "read_numpy_output_sync",
    "require_numpy",
    "write_numpy_output_async",
    "write_numpy_output_sync",
]
