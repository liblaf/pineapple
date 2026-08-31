# liblaf.cache

`liblaf.cache` is a local, directory-backed cache for expensive Python work.
Each ready key is an inspectable directory containing `inputs.txt`, a payload,
and `metadata.json`. A temporary directory is published atomically only after
all of those files are ready.

```python
from pathlib import Path
from liblaf.cache import Cache, Purge, SyncFolderStorage, cache

storage = SyncFolderStorage(".cache/results")


@cache(storage=storage, key=lambda path: str(Path(path).resolve()))
def load(path: str) -> dict[str, object]:
    return {"path": path}


assert load("input.txt") == load("input.txt")

values = Cache(".cache/values")
values["answer"] = {"value": 42}
assert values["answer"] == {"value": 42}
```

The decorator also accepts `inputs_writer`, `output_writer`, `output_reader`,
and `purge` directly when a separate storage object would be unnecessary.
`Purge(size="4G")` is the default LRU policy; its size suffixes use binary
multipliers.

For a disposable per-user cache, the decorator needs no boilerplate. Its
default key is `joblib.hash((function identity, args, kwargs))`, so unrelated
functions cannot collide even when their arguments are equal.

```python
from liblaf.cache import cache


@cache
def expensive(value: int) -> object:
    return object()
```

Use `AsyncFolderStorage` with `cache_async`, or `AsyncCache` with its
`await get/set/delete` methods, for asynchronous work. The async API does not
pretend that Python's synchronous `Mapping` protocol is awaitable.

## Choose an API

- Use `@cache` or `@cache_async` for a function whose result can be discarded
  and recomputed.
- Use `Cache` or `AsyncCache` for simple key/value access.
- Use `SyncFolderStorage` or `AsyncFolderStorage` when callers need explicit
  keys, metadata inspection, custom codecs, or single-flight coordination.

`cache_method` and `cache_method_async` keep storage ownership on an object:
pass a storage attribute name and a key function that receives the instance.

## Contract

- Callers provide a deterministic string key before an entry directory is
  selected. The key is hashed for the directory name and retained in the
  manifest for inspection.
- Decorated calls acquire a per-key local-filesystem lock, re-check the cache,
  and publish only on success. A live owner prevents duplicate computation;
  cancellation or process death releases the lock and a later call may compute
  again. This is single-flight, not exactly-once side-effect execution.
- JSON is preferred; bytes, NumPy arrays and mappings of arrays use native
  files. Optional PyVista, Torch, Pandas, and Polars objects use VTK, Torch,
  and Parquet files. Unsupported objects use required `output.joblib.gz` as a
  last resort. Never read untrusted cache directories.
- `inputs.txt` uses `liblaf.pprint` when it is installed and standard-library
  `pprint` otherwise; this optional adapter never becomes a package dependency.
- Every entry has schema-versioned `metadata.json`. Missing, malformed, or
  mismatched manifests raise `CorruptEntryError`; they are not cache misses.
- LRU purge is enabled by default with a 4 GiB limit. It runs after publication;
  pending temporary directories and active key locks are never candidates.

The initial backend targets local filesystems. Network filesystems and durable
application state are out of scope; use a database or dedicated store for data
that must never be evicted.

Read the [storage guide](https://liblaf.github.io/cache/guides/storage/),
[codec guide](https://liblaf.github.io/cache/guides/codecs/),
[single-flight concept](https://liblaf.github.io/cache/concepts/single-flight/),
[domain context](https://github.com/liblaf/cache/blob/main/CONTEXT.md), and
[architecture decisions](https://github.com/liblaf/cache/tree/main/docs/adr).

## License

[MIT](https://github.com/liblaf/cache/blob/main/LICENSE)
