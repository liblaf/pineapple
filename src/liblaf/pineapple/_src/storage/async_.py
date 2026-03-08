from __future__ import annotations

import importlib
import os
import pathlib
import time
import uuid
from collections.abc import Callable
from typing import Any, cast

import anyio
import msgspec

from liblaf.pineapple._src.io.json import (
    read_json_output_async,
    write_json_output_async,
)
from liblaf.pineapple._src.io.numpy import (
    read_numpy_output_async,
    write_numpy_output_async,
)
from liblaf.pineapple._src.io.pickle import (
    read_pickle_output_async,
    write_pickle_output_async,
)
from liblaf.pineapple._src.io.repr import write_repr_inputs_async
from liblaf.pineapple._src.keying import key_to_relpath, validate_key
from liblaf.pineapple._src.shared import (
    AsyncInputsWriter,
    AsyncKeyLockPool,
    AsyncOutputReader,
    AsyncOutputWriter,
)
from liblaf.pineapple._src.shared.fs import directory_size_bytes, safe_rmtree
from liblaf.pineapple._src.storage.index import IndexStore
from liblaf.pineapple._src.storage.metadata import write_metadata_atomic_async
from liblaf.pineapple._src.storage.policies import PrunePolicy


async def _run_sync[T](func: Callable[..., T], *args: Any) -> T:
    run_sync: Any = cast("Any", anyio.to_thread).run_sync
    value: T = await run_sync(func, *args)
    return value


async def _default_inputs_writer(folder: anyio.Path, *args: Any, **kwargs: Any) -> None:
    await write_repr_inputs_async(folder, *args, **kwargs)


def _load_numpy() -> Any | None:
    module: Any | None
    try:
        module = importlib.import_module("numpy")
    except ModuleNotFoundError:  # pragma: no cover - optional dependency
        return None
    return module


async def _default_output_writer(folder: anyio.Path, output: Any) -> None:
    for output_file in ("output.json", "output.npy", "output.pkl", "output.bin"):
        await (folder / output_file).unlink(missing_ok=True)

    if isinstance(output, (bytes, bytearray)):
        payload: bytes = bytes(output)
        await (folder / "output.bin").write_bytes(payload)
        return

    numpy_module: Any | None = _load_numpy()
    if numpy_module is not None and isinstance(output, numpy_module.ndarray):
        await write_numpy_output_async(folder, output)
        return

    try:
        await write_json_output_async(folder, output)
    except (TypeError, ValueError, msgspec.EncodeError):
        await write_pickle_output_async(folder, output)


async def _default_output_reader(folder: anyio.Path) -> Any:
    binary_path = folder / "output.bin"
    if await binary_path.exists():
        return await binary_path.read_bytes()
    json_path = folder / "output.json"
    if await json_path.exists():
        return await read_json_output_async(folder)
    numpy_path = folder / "output.npy"
    if await numpy_path.exists():
        return await read_numpy_output_async(folder)
    pickle_path = folder / "output.pkl"
    if await pickle_path.exists():
        return await read_pickle_output_async(folder)
    msg: str = f"no output file found under {folder}"
    raise FileNotFoundError(msg)


class AsyncFolderStorage:
    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        inputs_writer: AsyncInputsWriter | None = None,
        output_writer: AsyncOutputWriter | None = None,
        output_reader: AsyncOutputReader[Any] | None = None,
        prune_policy: PrunePolicy | None = None,
    ) -> None:
        self._root = pathlib.Path(path)
        self._root.mkdir(parents=True, exist_ok=True)

        self._inputs_writer = inputs_writer or _default_inputs_writer
        self._output_writer = output_writer or _default_output_writer
        self._output_reader = output_reader or _default_output_reader
        self._prune_policy = prune_policy

        self._index = IndexStore(self._root / ".pineapple-index.sqlite3")
        self._index.ensure_schema()

        self._locks = AsyncKeyLockPool()

    async def put(
        self,
        key: str,
        *,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        output: Any,
        user_metadata: dict[str, Any] | None = None,
    ) -> None:
        normalized_key = validate_key(key)
        entry_path = self._entry_path(normalized_key)

        temp_key = normalized_key.replace("/", "__")
        stage_path = anyio.Path(str(self._root / f"{temp_key}.{uuid.uuid4().hex}.tmp"))
        await stage_path.mkdir(parents=False, exist_ok=False)

        try:
            await self._inputs_writer(stage_path, *args, **kwargs)
            await self._output_writer(stage_path, output)
            await write_metadata_atomic_async(
                folder=stage_path,
                key=normalized_key,
                user_metadata=user_metadata,
            )
            await self._commit_stage(
                key=normalized_key,
                stage_path=stage_path,
                entry_path=entry_path,
            )
        except Exception:
            await _run_sync(safe_rmtree, pathlib.Path(str(stage_path)))
            raise

        if self._prune_policy is not None:
            await self.prune()

    async def get(self, key: str) -> Any | None:
        normalized_key = validate_key(key)
        has_entry: bool = await _run_sync(
            lambda: self._index.has_entry(key=normalized_key)
        )
        if not has_entry:
            return None
        entry_path = anyio.Path(str(self._entry_path(normalized_key)))
        if not await entry_path.exists():
            return None
        value = await self._output_reader(entry_path)
        await _run_sync(
            lambda: self._index.touch_entry(
                key=normalized_key,
                atime_ns=time.time_ns(),
            )
        )
        return value

    async def delete(self, key: str) -> None:
        normalized_key = validate_key(key)
        await _run_sync(safe_rmtree, self._entry_path(normalized_key))
        await _run_sync(self._index.delete_keys, [normalized_key])

    async def prune(self) -> None:
        if self._prune_policy is None:
            return
        total_bytes, total_entries = await _run_sync(self._index.totals)
        lru_entries: list[tuple[str, int]] = await _run_sync(
            lambda: list(self._index.iter_lru())
        )
        keys = self._prune_policy.select_keys(
            total_bytes=total_bytes,
            total_entries=total_entries,
            lru_entries=lru_entries,
        )
        for key in keys:
            await _run_sync(safe_rmtree, self._entry_path(key))
        await _run_sync(self._index.delete_keys, keys)

    def _entry_path(self, key: str) -> pathlib.Path:
        return self._root / key_to_relpath(key)

    async def _commit_stage(
        self, *, key: str, stage_path: anyio.Path, entry_path: pathlib.Path
    ) -> None:
        lock = await self._locks.get(key)
        async with lock:
            await _run_sync(
                lambda: entry_path.parent.mkdir(parents=True, exist_ok=True)
            )
            backup_path = entry_path.with_name(
                f"{entry_path.name}.old.{uuid.uuid4().hex}.tmp"
            )
            had_existing: bool = await _run_sync(entry_path.exists)
            if had_existing:
                await _run_sync(entry_path.replace, backup_path)
            await _run_sync(pathlib.Path(str(stage_path)).replace, entry_path)
            try:
                size_bytes: int = await _run_sync(directory_size_bytes, entry_path)
                await _run_sync(
                    lambda: self._index.upsert_entry(
                        key=key,
                        size_bytes=size_bytes,
                        atime_ns=time.time_ns(),
                    )
                )
            except Exception:
                await _run_sync(safe_rmtree, entry_path)
                if had_existing and await _run_sync(backup_path.exists):
                    await _run_sync(backup_path.replace, entry_path)
                raise
            finally:
                await _run_sync(safe_rmtree, backup_path)


__all__ = ["AsyncFolderStorage"]
