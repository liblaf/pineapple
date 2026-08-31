# Storage and entries

`SyncFolderStorage` and `AsyncFolderStorage` are the explicit APIs behind the
decorators. They are appropriate when the application already owns a cache
root, wants meaningful string keys, or needs to inspect entries.

```python
from liblaf.cache import SyncFolderStorage

storage = SyncFolderStorage(".cache/results")
storage.put("report/2026-09-01", args=(), kwargs={}, output={"ok": True})

assert storage.contains("report/2026-09-01")
assert storage.get("report/2026-09-01") == {"ok": True}
```

Keys are stripped of surrounding whitespace, must not be empty, and are
hashed into a stable three-level relative path. The human-readable key remains
in `metadata.json`; it is not used directly as a filename.

## Publication and corruption

Writers stage a sibling directory, write input and output artifacts, add the
manifest, and publish it atomically. A reader never treats a partially written
directory as a hit. In contrast, a missing or invalid manifest for an indexed
entry raises `CorruptEntryError`: corruption is visible rather than silently
recomputed.

`get()` returns `None` only for an absent key. `Cache.__getitem__` and
`AsyncCache.get()` translate an absent key into `KeyError` for mapping-style
callers.

## Pruning

Every storage has an LRU `Purge(size="4G")` policy by default. After a
successful publication, it removes least-recently-used ready entries until
the size and optional entry-count limits are met. Pruning skips keys with an
active filesystem lock; a running computation is never an eviction target.
