from __future__ import annotations

import importlib
import pathlib
import time
import uuid
from typing import Any

import msgspec

from liblaf.pineapple._src.io.json import read_json_output_sync, write_json_output_sync
from liblaf.pineapple._src.io.numpy import (
    read_numpy_output_sync,
    write_numpy_output_sync,
)
from liblaf.pineapple._src.io.pickle import (
    read_pickle_output_sync,
    write_pickle_output_sync,
)
from liblaf.pineapple._src.io.repr import write_repr_inputs_sync
from liblaf.pineapple._src.keying import key_to_relpath, validate_key
from liblaf.pineapple._src.shared import (
    KeyLockPool,
    OutputReader,
    SyncInputsWriter,
    SyncOutputWriter,
)
from liblaf.pineapple._src.shared.fs import directory_size_bytes, safe_rmtree
from liblaf.pineapple._src.storage.index import IndexStore
from liblaf.pineapple._src.storage.metadata import write_metadata_atomic_sync
from liblaf.pineapple._src.storage.policies import PrunePolicy


def _default_inputs_writer(folder: pathlib.Path, *args: Any, **kwargs: Any) -> None:
    write_repr_inputs_sync(folder, *args, **kwargs)


def _load_numpy() -> Any | None:
    module: Any | None
    try:
        module = importlib.import_module("numpy")
    except ModuleNotFoundError:  # pragma: no cover - optional dependency
        return None
    return module


def _default_output_writer(folder: pathlib.Path, output: Any) -> None:
    for output_file in ("output.json", "output.npy", "output.pkl", "output.bin"):
        (folder / output_file).unlink(missing_ok=True)

    if isinstance(output, (bytes, bytearray)):
        payload: bytes = bytes(output)
        (folder / "output.bin").write_bytes(payload)
        return

    numpy_module: Any | None = _load_numpy()
    if numpy_module is not None and isinstance(output, numpy_module.ndarray):
        write_numpy_output_sync(folder, output)
        return

    try:
        write_json_output_sync(folder, output)
    except (TypeError, ValueError, msgspec.EncodeError):
        write_pickle_output_sync(folder, output)


def _default_output_reader(folder: pathlib.Path) -> Any:
    binary_path = folder / "output.bin"
    if binary_path.exists():
        return binary_path.read_bytes()
    json_path = folder / "output.json"
    if json_path.exists():
        return read_json_output_sync(folder)
    numpy_path = folder / "output.npy"
    if numpy_path.exists():
        return read_numpy_output_sync(folder)
    pickle_path = folder / "output.pkl"
    if pickle_path.exists():
        return read_pickle_output_sync(folder)
    msg: str = f"no output file found under {folder}"
    raise FileNotFoundError(msg)


class SyncFolderStorage:
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

        self._inputs_writer = inputs_writer or _default_inputs_writer
        self._output_writer = output_writer or _default_output_writer
        self._output_reader = output_reader or _default_output_reader
        self._prune_policy = prune_policy

        self._index = IndexStore(self._root / ".pineapple-index.sqlite3")
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
        normalized_key = validate_key(key)
        if not self._index.has_entry(key=normalized_key):
            return None
        entry_path = self._entry_path(normalized_key)
        if not entry_path.exists():
            return None
        value = self._output_reader(entry_path)
        self._index.touch_entry(key=normalized_key, atime_ns=time.time_ns())
        return value

    def delete(self, key: str) -> None:
        normalized_key = validate_key(key)
        safe_rmtree(self._entry_path(normalized_key))
        self._index.delete_keys([normalized_key])

    def prune(self) -> None:
        if self._prune_policy is None:
            return
        total_bytes, total_entries = self._index.totals()
        keys = self._prune_policy.select_keys(
            total_bytes=total_bytes,
            total_entries=total_entries,
            lru_entries=self._index.iter_lru(),
        )
        for key in keys:
            safe_rmtree(self._entry_path(key))
        self._index.delete_keys(keys)

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
