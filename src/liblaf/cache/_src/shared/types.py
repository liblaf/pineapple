from __future__ import annotations

import pathlib
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import anyio


class OutputReader[T](Protocol):
    def __call__(self, folder: pathlib.Path) -> T: ...


class AsyncOutputReader[T](Protocol):
    def __call__(self, folder: anyio.Path) -> Awaitable[T]: ...


class SyncInputsWriter(Protocol):
    def __call__(self, folder: pathlib.Path, *args: Any, **kwargs: Any) -> None: ...


class SyncOutputWriter(Protocol):
    def __call__(self, folder: pathlib.Path, output: Any) -> None: ...


class AsyncInputsWriter(Protocol):
    def __call__(
        self, folder: anyio.Path, *args: Any, **kwargs: Any
    ) -> Awaitable[None]: ...


class AsyncOutputWriter(Protocol):
    def __call__(self, folder: anyio.Path, output: Any) -> Awaitable[None]: ...


KeyBuilder = Callable[..., str]


__all__ = [
    "AsyncInputsWriter",
    "AsyncOutputReader",
    "AsyncOutputWriter",
    "KeyBuilder",
    "OutputReader",
    "SyncInputsWriter",
    "SyncOutputWriter",
]
