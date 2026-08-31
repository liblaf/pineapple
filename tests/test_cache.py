from __future__ import annotations

import asyncio
import json
import multiprocessing
import shutil
import sqlite3
import sys
import time
import types
from pathlib import Path

import pytest

from liblaf.cache import (
    AsyncCache,
    AsyncFolderStorage,
    Cache,
    CorruptEntryError,
    LRUMaxPolicy,
    Purge,
    SyncFolderStorage,
    cache,
    cache_async,
)
from liblaf.cache._src.storage.index.sqlite import open_sqlite


class JoblibOutput:
    def __init__(self) -> None:
        self.answer = 42


def test_index_connection_context_closes_connection(tmp_path: Path) -> None:
    """SQLite index connections are unusable once their transaction scope exits."""
    with open_sqlite(tmp_path / "index.sqlite3") as conn:
        conn.execute("SELECT 1")

    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        conn.execute("SELECT 1")


def _contended_call(
    root: str, counter: str, result: multiprocessing.Queue[int]
) -> None:
    storage = SyncFolderStorage(root)

    def key(_: int) -> str:
        return "shared"

    @cache(storage=storage, key=key)
    def compute(_: int) -> int:
        with Path(counter).open("a", encoding="utf-8") as stream:
            stream.write("run\n")
        time.sleep(0.1)
        return 42

    result.put(compute(1))


def test_sync_decorator_publishes_one_ready_directory(tmp_path: Path) -> None:
    storage = SyncFolderStorage(tmp_path)
    calls = 0

    def key(value: int) -> str:
        return str(value)

    @cache(storage=storage, key=key)
    def twice(value: int) -> int:
        nonlocal calls
        calls += 1
        return value * 2

    assert twice(2) == 4
    assert twice(2) == 4
    assert calls == 1
    entries = list(tmp_path.glob("*/*/*/metadata.json"))
    assert len(entries) == 1
    assert json.loads(entries[0].read_text())["key"] == "2"

    def none_key() -> str:
        return "none"

    @cache(storage=storage, key=none_key)
    def none() -> None:
        return None

    assert none() is None


def test_decorator_defaults_use_joblib_hash_and_user_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        "liblaf.cache._src.decorators.sync.platformdirs.user_cache_dir",
        lambda _name: str(tmp_path),
    )
    calls = 0

    @cache
    def compute(value: int) -> int:
        nonlocal calls
        calls += 1
        return value * 2

    assert compute(3) == 6
    assert compute(3) == 6
    assert calls == 1


def test_async_decorator_defaults_use_joblib_hash_and_user_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        "liblaf.cache._src.decorators.async_.platformdirs.user_cache_dir",
        lambda _name: str(tmp_path),
    )

    async def run() -> None:
        calls = 0

        @cache_async
        async def compute(value: int) -> int:
            nonlocal calls
            calls += 1
            return value * 2

        assert await compute(3) == 6
        assert await compute(3) == 6
        assert calls == 1

    asyncio.run(run())


def test_async_decorator_is_single_flight_with_concurrent_tasks(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        calls = 0

        @cache_async(storage=AsyncFolderStorage(tmp_path), key=lambda _value: "key")
        async def compute(value: int) -> int:
            nonlocal calls
            calls += 1
            await asyncio.sleep(0.01)
            return value * 2

        assert await asyncio.gather(compute(3), compute(3)) == [6, 6]
        assert calls == 1

    asyncio.run(run())


def test_mapping_and_corruption_are_visible(tmp_path: Path) -> None:
    values = Cache(tmp_path)
    values["answer"] = {"value": 42}
    assert values["answer"] == {"value": 42}
    manifest = next(tmp_path.glob("*/*/*/metadata.json"))
    manifest.write_text("not json")
    with pytest.raises(CorruptEntryError):
        _ = values["answer"]


def test_missing_or_invalid_output_is_corruption(tmp_path: Path) -> None:
    values = Cache(tmp_path)
    values["answer"] = {"value": 42}
    output = next(tmp_path.glob("*/*/*/output.json"))
    output.write_text("not json")

    with pytest.raises(CorruptEntryError, match="invalid cache output"):
        _ = values["answer"]


def test_missing_indexed_directory_is_corruption(tmp_path: Path) -> None:
    storage = SyncFolderStorage(tmp_path)
    storage.put("answer", args=(), kwargs={}, output=42)
    entry = next(tmp_path.glob("*/*/*"))
    shutil.rmtree(entry)

    with pytest.raises(CorruptEntryError, match="directory is missing"):
        storage.contains("answer")


def test_async_cache_round_trip(tmp_path: Path) -> None:
    async def run() -> None:
        values = AsyncCache(tmp_path)
        await values.set("answer", {"value": 42})
        assert await values.get("answer") == {"value": 42}

    asyncio.run(run())


def test_processes_single_flight_and_stale_stages_do_not_block(tmp_path: Path) -> None:
    counter = tmp_path / "counter.txt"
    (tmp_path / "orphan.tmp").mkdir()
    context = multiprocessing.get_context("fork")
    results: multiprocessing.Queue[int] = context.Queue()
    processes = [
        context.Process(
            target=_contended_call, args=(str(tmp_path), str(counter), results)
        )
        for _ in range(2)
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=10)
        assert process.exitcode == 0
    assert sorted(results.get(timeout=1) for _ in processes) == [42, 42]
    assert counter.read_text().splitlines() == ["run"]


def test_purge_and_builtin_format_round_trips(tmp_path: Path) -> None:
    storage = SyncFolderStorage(tmp_path, prune_policy=LRUMaxPolicy(max_bytes=1))
    storage.put("large", args=(), kwargs={}, output=b"too large")
    assert storage.get("large") is None
    values = Cache(tmp_path / "formats")
    values["json"] = {"ok": True}
    values["bytes"] = b"payload"
    assert values["json"] == {"ok": True}
    assert values["bytes"] == b"payload"


def test_joblib_is_the_only_last_resort_serializer(tmp_path: Path) -> None:
    values = Cache(tmp_path)
    values["object"] = JoblibOutput()

    entry = next(tmp_path.glob("*/*/*"))
    assert (entry / "output.joblib.gz").exists()
    assert not (entry / "output.pkl").exists()
    assert values["object"].answer == 42


def test_numpy_array_mapping_uses_compressed_npz(tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    values = Cache(tmp_path)
    values["arrays"] = {"left": np.arange(2), "right": np.arange(3)}

    entry = next(tmp_path.glob("*/*/*"))
    assert (entry / "output.npz").exists()
    restored = values["arrays"]
    assert np.array_equal(restored["left"], np.arange(2))


def test_numpy_object_array_uses_joblib(tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    values = Cache(tmp_path)
    values["objects"] = np.array([{"answer": 42}], dtype=object)

    entry = next(tmp_path.glob("*/*/*"))
    assert (entry / "output.joblib.gz").exists()
    assert values["objects"].item() == {"answer": 42}


def test_purge_accepts_human_readable_binary_sizes() -> None:
    purge = Purge(size="1.5 KiB")

    assert purge.select_keys(
        total_bytes=1537,
        total_entries=2,
        lru_entries=[("old", 1), ("new", 1536)],
    ) == ["old"]


def test_decorator_accepts_direct_io_and_purge_options(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        "liblaf.cache._src.decorators.sync.platformdirs.user_cache_dir",
        lambda _name: str(tmp_path),
    )
    calls = 0

    def write_inputs(folder: Path, value: int) -> None:
        (folder / "inputs.custom").write_text(str(value))

    def write_output(folder: Path, output: int) -> None:
        (folder / "output.custom").write_text(str(output))

    def read_output(folder: Path) -> int:
        return int((folder / "output.custom").read_text())

    @cache(
        inputs_writer=write_inputs,
        output_writer=write_output,
        output_reader=read_output,
        purge=Purge(size="1 MiB"),
        key=str,
    )
    def compute(value: int) -> int:
        nonlocal calls
        calls += 1
        return value * 2

    assert compute(3) == 6
    assert compute(3) == 6
    assert calls == 1
    entry = next(tmp_path.glob("*/*/*"))
    assert (entry / "inputs.custom").read_text() == "3"
    assert (entry / "output.custom").read_text() == "6"


def test_decorator_prunes_after_releasing_its_key_lock(tmp_path: Path) -> None:
    storage = SyncFolderStorage(tmp_path, prune_policy=Purge(size=1))

    @cache(storage=storage, key=lambda: "large")
    def compute() -> bytes:
        return b"larger than one byte"

    assert compute() == b"larger than one byte"
    assert not storage.contains("large")


def test_polars_adapter_uses_write_parquet(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = types.ModuleType("polars")

    class DataFrame:
        def __init__(self, value: str) -> None:
            self.value = value

        def write_parquet(self, path: Path) -> None:
            path.write_text(self.value)

    def read_parquet(path: Path) -> DataFrame:
        return DataFrame(path.read_text())

    module.__dict__.update(DataFrame=DataFrame, read_parquet=read_parquet)
    monkeypatch.setitem(sys.modules, "polars", module)
    values = Cache(tmp_path)

    values["frame"] = DataFrame("table")

    entry = next(tmp_path.glob("*/*/*"))
    assert (entry / "output.parquet").read_text() == "table"
    restored = values["frame"]
    assert isinstance(restored, DataFrame)
    assert restored.value == "table"
