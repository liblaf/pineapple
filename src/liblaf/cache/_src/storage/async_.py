from __future__ import annotations

import os
import pathlib
import time
import uuid
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any, cast

import anyio
from filelock import FileLock

from liblaf.cache._src.io.output import (
    read_default_output_sync,
    write_default_output_sync,
)
from liblaf.cache._src.io.repr import write_repr_inputs_async
from liblaf.cache._src.keying import key_to_relpath, validate_key
from liblaf.cache._src.shared import (
    AsyncInputsWriter,
    AsyncKeyLockPool,
    AsyncOutputReader,
    AsyncOutputWriter,
)
from liblaf.cache._src.shared.fs import directory_size_bytes, safe_rmtree
from liblaf.cache._src.storage.index import IndexStore
from liblaf.cache._src.storage.metadata import (
    CorruptEntryError,
    read_metadata_sync,
    write_metadata_atomic_async,
)
from liblaf.cache._src.storage.policies import PrunePolicy, Purge
from liblaf.cache._src.storage.sync import _lock_path, _try_prune_key


async def _run_sync[T](func: Callable[..., T], *args: Any) -> T:
    run_sync: Any = cast("Any", anyio.to_thread).run_sync
    value: T = await run_sync(func, *args)
    return value


async def _default_inputs_writer(folder: anyio.Path, *args: Any, **kwargs: Any) -> None:
    await write_repr_inputs_async(folder, *args, **kwargs)


async def _default_output_writer(folder: anyio.Path, output: Any) -> None:
    await _run_sync(write_default_output_sync, pathlib.Path(str(folder)), output)


async def _default_output_reader(folder: anyio.Path) -> Any:
    return await _run_sync(read_default_output_sync, pathlib.Path(str(folder)))


class AsyncFolderStorage:
    """Awaitable local-directory storage with the `SyncFolderStorage` contract.

    Args:
        path: Cache root directory, created if necessary.
        inputs_writer: Awaitable writer for inspectable call inputs.
        output_writer: Awaitable writer for a computed output.
        output_reader: Awaitable reader for a stored output.
        prune_policy: Optional LRU-like policy. Omit it for `Purge(size="4G")`.
    """

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        inputs_writer: AsyncInputsWriter | None = None,
        output_writer: AsyncOutputWriter | None = None,
        output_reader: AsyncOutputReader[Any] | None = None,
        prune_policy: PrunePolicy | None = None,
    ) -> None:
        """Atomically publish one output under `key`."""
        self._root = pathlib.Path(path)
        self._root.mkdir(parents=True, exist_ok=True)

        self._inputs_writer = (
            _default_inputs_writer if inputs_writer is None else inputs_writer
        )
        self._output_writer = (
            _default_output_writer if output_writer is None else output_writer
        )
        self._output_reader = (
            _default_output_reader if output_reader is None else output_reader
        )
        self._prune_policy = Purge() if prune_policy is None else prune_policy

        self._index = IndexStore(self._root / ".cache-index.sqlite3")
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
        """Return the stored output, `None` for a miss, or raise on corruption."""
        normalized_key = validate_key(key)
        has_entry: bool = await _run_sync(
            lambda: self._index.has_entry(key=normalized_key)
        )
        if not has_entry:
            return None
        entry_path = anyio.Path(str(self._entry_path(normalized_key)))
        if not await entry_path.is_dir():
            message = f"indexed cache entry directory is missing: {entry_path}"
            raise CorruptEntryError(message)
        await _run_sync(
            lambda: read_metadata_sync(
                folder=pathlib.Path(str(entry_path)), key=normalized_key
            )
        )
        try:
            value = await self._output_reader(entry_path)
        except Exception as error:
            message = f"invalid cache output: {entry_path}"
            raise CorruptEntryError(message) from error
        await _run_sync(
            lambda: self._index.touch_entry(
                key=normalized_key,
                atime_ns=time.time_ns(),
            )
        )
        return value

    async def contains(self, key: str) -> bool:
        normalized_key = validate_key(key)
        if not await _run_sync(lambda: self._index.has_entry(key=normalized_key)):
            return False
        path = pathlib.Path(str(self._entry_path(normalized_key)))
        if not await _run_sync(path.is_dir):
            message = f"indexed cache entry directory is missing: {path}"
            raise CorruptEntryError(message)
        await _run_sync(lambda: read_metadata_sync(folder=path, key=normalized_key))
        return True

    @asynccontextmanager
    async def lock(self, key: str) -> AsyncGenerator[None]:
        """Acquire the local-filesystem key lock without blocking the event loop."""
        normalized_key = validate_key(key)
        path = _lock_path(self._root, normalized_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        lock = FileLock(path, thread_local=False)
        await _run_sync(lock.acquire)
        try:
            yield
        finally:
            await _run_sync(lock.release)

    async def delete(self, key: str) -> None:
        """Remove a ready entry and its index row if it exists."""
        normalized_key = validate_key(key)
        await _run_sync(safe_rmtree, self._entry_path(normalized_key))
        await _run_sync(self._index.delete_keys, [normalized_key])

    async def prune(self) -> None:
        """Remove unlocked LRU entries selected by this storage's policy."""
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
            await _run_sync(_try_prune_key, self._root, self._index, key)

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
