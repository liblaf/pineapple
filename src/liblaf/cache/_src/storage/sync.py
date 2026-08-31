from __future__ import annotations

import pathlib
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from filelock import FileLock, Timeout

from liblaf.cache._src.io.output import (
    read_default_output_sync,
    write_default_output_sync,
)
from liblaf.cache._src.io.repr import write_repr_inputs_sync
from liblaf.cache._src.keying import key_to_relpath, validate_key
from liblaf.cache._src.shared import (
    KeyLockPool,
    OutputReader,
    SyncInputsWriter,
    SyncOutputWriter,
)
from liblaf.cache._src.shared.fs import directory_size_bytes, safe_rmtree
from liblaf.cache._src.storage.index import IndexStore
from liblaf.cache._src.storage.metadata import (
    CorruptEntryError,
    read_metadata_sync,
    write_metadata_atomic_sync,
)
from liblaf.cache._src.storage.policies import PrunePolicy, Purge


def _lock_path(root: pathlib.Path, key: str) -> pathlib.Path:
    return root / ".locks" / f"{key_to_relpath(key).name}.lock"


def _try_prune_key(
    root: pathlib.Path,
    index: IndexStore,
    key: str,
) -> bool:
    path = _lock_path(root, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with FileLock(path, timeout=0):
            safe_rmtree(root / key_to_relpath(key))
            index.delete_keys([key])
    except Timeout:
        return False
    return True


def _default_inputs_writer(folder: pathlib.Path, *args: Any, **kwargs: Any) -> None:
    write_repr_inputs_sync(folder, *args, **kwargs)


def _default_output_writer(folder: pathlib.Path, output: Any) -> None:
    write_default_output_sync(folder, output)


def _default_output_reader(folder: pathlib.Path) -> Any:
    return read_default_output_sync(folder)


class SyncFolderStorage:
    """Store ready cache entries in a local directory tree.

    Writes stage a sibling directory and atomically publish it after inputs,
    output, and metadata are complete. `get()` returns `None` for a missing
    key and raises `CorruptEntryError` for an indexed but invalid entry.

    Args:
        path: Cache root directory, created if necessary.
        inputs_writer: Optional writer for inspectable call inputs.
        output_writer: Optional writer for a computed output.
        output_reader: Optional reader for a stored output.
        prune_policy: Optional LRU-like policy. Omit it for `Purge(size="4G")`.
    """

    def __init__(
        self,
        path: str | pathlib.Path,
        *,
        inputs_writer: SyncInputsWriter | None = None,
        output_writer: SyncOutputWriter | None = None,
        output_reader: OutputReader[Any] | None = None,
        prune_policy: PrunePolicy | None = None,
    ) -> None:
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

        self._locks = KeyLockPool()

    def put(
        self,
        key: str,
        *,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        output: Any,
        user_metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish one output under `key` after writing its inspection files.

        Args:
            key: Non-empty application cache key.
            args: Original positional call arguments for `inputs_writer`.
            kwargs: Original keyword call arguments for `inputs_writer`.
            output: Value passed to `output_writer`.
            user_metadata: Optional application-owned manifest metadata.
        """
        normalized_key = validate_key(key)
        entry_path = self._entry_path(normalized_key)

        temp_key = normalized_key.replace("/", "__")
        stage_path = self._root / f"{temp_key}.{uuid.uuid4().hex}.tmp"
        stage_path.mkdir(parents=False, exist_ok=False)

        try:
            self._inputs_writer(stage_path, *args, **kwargs)
            self._output_writer(stage_path, output)
            write_metadata_atomic_sync(
                folder=stage_path,
                key=normalized_key,
                user_metadata=user_metadata,
            )
            self._commit_stage(
                key=normalized_key, stage_path=stage_path, entry_path=entry_path
            )
        except Exception:
            safe_rmtree(stage_path)
            raise

        if self._prune_policy is not None:
            self.prune()

    def get(self, key: str) -> Any | None:
        """Return the stored output, `None` for a miss, or raise on corruption."""
        normalized_key = validate_key(key)
        if not self._index.has_entry(key=normalized_key):
            return None
        entry_path = self._entry_path(normalized_key)
        if not entry_path.is_dir():
            message = f"indexed cache entry directory is missing: {entry_path}"
            raise CorruptEntryError(message)
        read_metadata_sync(folder=entry_path, key=normalized_key)
        try:
            value = self._output_reader(entry_path)
        except Exception as error:
            message = f"invalid cache output: {entry_path}"
            raise CorruptEntryError(message) from error
        self._index.touch_entry(key=normalized_key, atime_ns=time.time_ns())
        return value

    def contains(self, key: str) -> bool:
        """Return whether ``key`` names a ready, manifest-valid entry."""
        normalized_key = validate_key(key)
        if not self._index.has_entry(key=normalized_key):
            return False
        path = self._entry_path(normalized_key)
        if not path.is_dir():
            message = f"indexed cache entry directory is missing: {path}"
            raise CorruptEntryError(message)
        read_metadata_sync(folder=path, key=normalized_key)
        return True

    @contextmanager
    def lock(self, key: str) -> Generator[None]:
        """Hold this local-filesystem key's inter-process single-flight lock."""
        normalized_key = validate_key(key)
        path = _lock_path(self._root, normalized_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(path):
            yield

    def is_locked(self, key: str) -> bool:
        """Return whether another owner currently holds ``key``'s lock."""
        normalized_key = validate_key(key)
        path = _lock_path(self._root, normalized_key)
        lock = FileLock(path, timeout=0)
        try:
            lock.acquire()
        except Timeout:
            return True
        lock.release()
        return False

    def delete(self, key: str) -> None:
        """Remove a ready entry and its index row if it exists."""
        normalized_key = validate_key(key)
        safe_rmtree(self._entry_path(normalized_key))
        self._index.delete_keys([normalized_key])

    def keys(self) -> list[str]:
        """Return the currently indexed ready-entry keys in LRU order."""
        return [key for key, _ in self._index.iter_lru()]

    def __len__(self) -> int:
        return self._index.totals()[1]

    def prune(self) -> None:
        """Remove unlocked LRU entries selected by this storage's policy."""
        if self._prune_policy is None:
            return
        total_bytes, total_entries = self._index.totals()
        keys = self._prune_policy.select_keys(
            total_bytes=total_bytes,
            total_entries=total_entries,
            lru_entries=self._index.iter_lru(),
        )
        for key in keys:
            _try_prune_key(self._root, self._index, key)

    def _entry_path(self, key: str) -> pathlib.Path:
        return self._root / key_to_relpath(key)

    def _commit_stage(
        self, *, key: str, stage_path: pathlib.Path, entry_path: pathlib.Path
    ) -> None:
        lock = self._locks.get(key)
        with lock:
            entry_path.parent.mkdir(parents=True, exist_ok=True)
            backup_path = entry_path.with_name(
                f"{entry_path.name}.old.{uuid.uuid4().hex}.tmp"
            )
            had_existing = entry_path.exists()
            if had_existing:
                entry_path.replace(backup_path)
            stage_path.replace(entry_path)
            try:
                self._index.upsert_entry(
                    key=key,
                    size_bytes=directory_size_bytes(entry_path),
                    atime_ns=time.time_ns(),
                )
            except Exception:
                safe_rmtree(entry_path)
                if had_existing and backup_path.exists():
                    backup_path.replace(entry_path)
                raise
            finally:
                safe_rmtree(backup_path)


__all__ = ["SyncFolderStorage"]
