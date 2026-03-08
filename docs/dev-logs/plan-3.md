# Plan 3: Global Index and Policy-Driven Pruning

Date: 2026-03-07
Status: Proposed
Scope: storage architecture redesign (`src/liblaf/pineapple/_src/storage/*`, docs, tests)

## Goal

Define a storage design that is robust under interruption, supports policy-based pruning (including LRU), and keeps customization boundaries clear:

- Reader customization: read output only.
- Writer customization: split into inputs writer (`folder, *args, **kwargs`) and output writer (`folder, output`).
- Metadata persistence: owned by storage, not customizable.
- Only metadata required by LRU pruning (for example `atime` and `size_bytes`): stored in a global index database.
- Entry writes: atomic via temp path + rename/replace.
- Decorator implementation: use `wrapt` to build decorator entrypoints and method variants.

No implementation changes are performed in this plan. This is the contract for subsequent coding.

## Design Principles

1. Single responsibility for codec hooks.

- `output_reader` reads only payload from an entry directory.
- `inputs_writer` writes input artifacts only.
- `output_writer` writes payload artifacts only.
- Storage writes metadata and manages index/pruning.

2. Two-layer metadata model.

- Per-entry metadata file (`metadata.json`) stores stable metadata that should not change on read.
- Global index database stores only minimal metadata required for LRU pruning and eviction.

3. Atomic commit semantics.

- New/updated entry is staged in a temp directory under the same parent as final path.
- Commit step is atomic rename/replace.
- Partial temp artifacts are cleaned on failure.

4. Policy-driven pruning.

- Pruning is policy-based (LRU first, extensible to other policies).
- Policy decisions read from the global index, not filesystem scans.

## Source Layout (Fresh Restart)

This layout is designed for a clean rebuild where `src/liblaf/pineapple` starts nearly empty.
The goal is to keep each module focused, preserve canonical public exports, and keep `_src` internal.

### Canonical public modules

- `src/liblaf/pineapple/__init__.py`
  - Canonical public exports for storage classes and policy types.
  - Re-export only; no implementation logic.
- `src/liblaf/pineapple/keys.py`
  - Canonical public exports for key helpers.
  - Re-export only; no implementation logic.

### Internal implementation tree

```text
src/liblaf/pineapple/
  __init__.py
  keys.py
  _src/
    __init__.py
    keying/
      __init__.py
      derive.py                  # key validation + deterministic key -> relative path
    io/
      __init__.py
      numpy.py                   # numpy reader + writer implementations
      json.py                    # json reader + writer implementations
      pickle.py                  # pickle reader + writer implementations
      repr.py                    # repr-based input writer implementation
    decorators/
      __init__.py
      sync.py                    # sync cache decorator entrypoints
      async_.py                  # async cache decorator entrypoints
      method.py                  # method decorator variants (sync + async helpers)
      core.py                    # shared call flow (key resolution, get/compute/put) built on wrapt
    shared/
      __init__.py
      fs.py                      # shared fs helpers (size scan, safe remove, atomic write)
      locking.py                 # key-lock registry + prune lock helpers
    storage/
      __init__.py
      sync.py                    # SyncFolderStorage orchestration
      async_.py                  # AsyncFolderStorage orchestration
      index/
        __init__.py
        schema.py                # sqlite schema management and versioning hooks
        store.py                 # IndexStore API (upsert/touch/totals/lru/delete)
        sqlite.py                # sqlite connection + pragma helpers
      policies/
        __init__.py
        protocol.py              # PrunePolicy protocol
        lru.py                   # LRU policy implementation(s)
      metadata/
        __init__.py
        models.py                # pydantic metadata models (EntryMetadataModel)
        serde.py                 # metadata read/write helpers for metadata.json
```

### Responsibility boundaries

- `keying/derive.py`
  - Validate key shape.
  - Convert key to deterministic relative path.
  - Must not depend on storage/index modules.
- `io/numpy.py`, `io/json.py`, `io/pickle.py`, and `io/repr.py`
  - Format-scoped I/O modules under one dedicated internal folder (`_src/io/*`).
  - `numpy/json/pickle` modules each implement both reader and writer functions for their format.
  - `repr.py` provides writer functions that persist `repr(...)` of inputs for inspection/debugging.
  - Modules may expose sync and async variants when needed by storage/decorators.
  - No runtime storage/index behavior.
- `decorators/sync.py`, `decorators/async_.py`, `decorators/method.py`
  - Public decorator integration layer over storage APIs.
  - Must be implemented using `wrapt` (for function and method decoration stability).
  - Must not implement metadata/index persistence directly.
- `decorators/core.py`
  - Shared decorator workflow primitives (resolve key, lookup, compute, commit, touch).
  - Keeps sync/async/method wrappers small and behavior-aligned.
  - Contains reusable `wrapt` integration helpers to avoid duplicated decoration mechanics.
- `storage/metadata/models.py`
  - Owns metadata schema and Pydantic serialization/validation behavior.
  - Defines stable per-entry metadata only (`key`, `ctime`, `user`).
- `storage/metadata/serde.py`
  - Owns read/write helpers for `metadata.json` commit markers.
  - Centralizes atomic write/read validation logic used by both sync and async storage.
- `storage/index/schema.py`
  - Owns sqlite schema lifecycle and versioning hooks for the global index DB.
- `storage/index/store.py`
  - Owns typed index operations used by storage and policies.
  - Exposes stage-oriented methods only (no raw connection leakage).
- `storage/index/sqlite.py`
  - Owns sqlite connection and pragma setup (WAL, foreign keys, busy timeout).
- `storage/policies/protocol.py`
  - Defines pruning decision contracts.
  - Must not perform filesystem mutations directly.
- `storage/policies/lru.py`
  - Implements LRU selection strategies using index-derived metadata.
  - Contains resource-limit policies (`max_bytes`, `max_entries`) and victim selection logic.
- `shared/fs.py`
  - Shared helpers for directory size accounting and robust recursive delete.
  - Keeps sync and async orchestration modules small.
- `shared/locking.py`
  - Encapsulates lock registry behavior so sync/async storage classes do not duplicate lock-table logic.
  - Defines lock ordering helpers used by pruning.
- `storage/sync.py` and `storage/async_.py`
  - Orchestrate put/get/delete/prune flows.
  - Call into `storage/metadata/*`, `storage/index/*`, `shared/fs.py`, and `shared/locking.py` rather than duplicating internals.

### Staged implementation order

1. `keying/derive.py`, `io/numpy.py`, `io/json.py`, `io/pickle.py`, `io/repr.py`, `storage/metadata/models.py`.
2. `storage/index/schema.py`, `storage/index/sqlite.py`, and `storage/index/store.py` with stage-A methods (`ensure_schema`, `upsert_entry`, `touch_entry`).
3. `storage/metadata/serde.py` and `shared/fs.py` shared helpers.
4. `storage/sync.py` with atomic commit + index update.
5. `storage/async_.py` parity with sync behavior.
6. `storage/policies/protocol.py` and `storage/policies/lru.py` + prune wiring in sync/async storage.
7. `decorators/core.py`, `decorators/sync.py`, `decorators/async_.py`, and `decorators/method.py` integration (all using `wrapt`).
8. `shared/locking.py` extraction if lock complexity grows beyond inline readability.
9. Public re-export stabilization in `__init__.py` and `keys.py`.

### Module quality constraints

- Prefer file size target <= 300 lines per module.
- Keep implementation out of all `__init__.py` files.
- Keep `_src` internal and non-canonical for public imports.
- Require explicit type annotations for all variables, including local variables in function bodies.
- Avoid circular imports by enforcing one-way dependency flow:
  - `keying/*` -> none
  - `io/*` -> `typing`, `collections.abc`, path types, format libs (`json`, `pickle`, `numpy`)
  - `decorators/core.py` -> `storage/sync.py`, `storage/async_.py`, `keying/*`, `io/*`, `wrapt`
  - `decorators/sync.py`, `decorators/async_.py`, `decorators/method.py` -> `decorators/core.py`
  - `shared/fs.py` and `shared/locking.py` -> stdlib primitives only
  - `storage/metadata/models.py` -> `pydantic`
  - `storage/metadata/serde.py` -> `storage/metadata/models.py`, stdlib fs primitives
  - `storage/index/schema.py` -> `sqlite3`, `pathlib`
  - `storage/index/sqlite.py` -> `sqlite3`, `pathlib`
  - `storage/index/store.py` -> `storage/index/schema.py`, `storage/index/sqlite.py`
  - `storage/policies/protocol.py` -> `typing`, `collections.abc`
  - `storage/policies/lru.py` -> `storage/policies/protocol.py`, `storage/index/store.py`, `typing`, `collections.abc`
  - `storage/sync.py` and `storage/async_.py` -> all above storage modules

## Proposed API (Public)

### Storage constructors

```python
class SyncFolderStorage:
    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        inputs_writer: SyncInputsWriter | None = None,
        output_writer: SyncOutputWriter | None = None,
        output_reader: OutputReader[Any] | None = None,
        prune_policy: PrunePolicy | None = None,
    ) -> None: ...

class AsyncFolderStorage:
    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        inputs_writer: AsyncInputsWriter | None = None,
        output_writer: AsyncOutputWriter | None = None,
        output_reader: AsyncOutputReader[Any] | None = None,
        prune_policy: PrunePolicy | None = None,
    ) -> None: ...
```

### I/O hook contracts

```python
class SyncInputsWriter(Protocol):
    def __call__(
        self,
        folder: pathlib.Path,
        *args: Any,
        **kwargs: Any,
    ) -> None: ...

class SyncOutputWriter(Protocol):
    def __call__(
        self,
        folder: pathlib.Path,
        output: Any,
    ) -> None: ...

class AsyncInputsWriter(Protocol):
    def __call__(
        self,
        folder: anyio.Path,
        *args: Any,
        **kwargs: Any,
    ) -> Awaitable[None]: ...

class AsyncOutputWriter(Protocol):
    def __call__(
        self,
        folder: anyio.Path,
        output: Any,
    ) -> Awaitable[None]: ...
```

Notes:

- `inputs_writer` owns input serialization only.
- `output_writer` owns output serialization only.
- The storage owns metadata writes and must always write `metadata.json` itself.
- Reader signatures remain output-only (`folder -> output`).
- Decorator entrypoints and method wrappers are implemented with `wrapt` to preserve signature/descriptor behavior.

### Put/get contracts

```python
def put(
    key: str,
    *,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    output: Any,
    user_metadata: dict[str, Any] | None = None,
) -> None

# async variant analogous
```

`library_metadata` is removed from public storage write API in this design.

## Metadata Model

### Per-entry `metadata.json` (stable)

Stored inside each entry folder and written by storage during commit:

```json
{
  "key": "...",
  "ctime": "2026-03-08T12:34:56.789123Z",
  "user": { "...": "..." }
}
```

Rules:

- Excludes mutable-on-read fields (`atime`, counters).
- Serves as write-time commit artifact and offline inspection/recovery hint.
- Updated only on `put`/replace, not `get`.
- Serialization/deserialization is handled by Pydantic models (for example `model_dump_json` on write and `model_validate_json` in maintenance/debug tooling), not ad-hoc dict/json code.
- Use timezone-aware `datetime` for stable timestamps in metadata (for example `ctime` in UTC); integer nanoseconds are reserved for LRU index fields like `atime_ns`.

Suggested internal model contract:

```python
class EntryMetadataModel(pydantic.BaseModel):
    key: str
    ctime: datetime.datetime
    user: dict[str, Any] = pydantic.Field(default_factory=dict)
```

### Global index database (LRU-minimal)

Database file: `<root>/.pineapple-index.sqlite3`

`entries` table (minimum):

- `key TEXT PRIMARY KEY`
- `size_bytes INTEGER NOT NULL`
- `atime_ns INTEGER NOT NULL`

Suggested indexes:

- `idx_entries_atime ON entries(atime_ns)`

Rules:

- Entry path is derived deterministically from `key`; do not store redundant path columns in DB.
- Keep DB columns limited to what LRU needs: ordering (`atime_ns`) and space accounting (`size_bytes`), keyed by `key`.
- Do not mirror per-entry stable metadata (for example `ctime` or user metadata) into the DB.

SQLite mode recommendations:

- WAL mode.
- Foreign keys on.
- Busy timeout configured.

### Index access layer (developer experience)

All SQL operations should be wrapped in a dedicated internal class instead of being spread across storage/policy code.

Proposed internal class (stage-oriented API):

```python
class IndexStore:
    def __init__(self, db_path: pathlib.Path) -> None: ...

    # Stage A: required for put/get runtime
    def ensure_schema(self) -> None: ...
    def upsert_entry(
        self,
        *,
        key: str,
        size_bytes: int,
        atime_ns: int,
    ) -> None: ...
    def touch_entry(self, *, key: str, atime_ns: int) -> None: ...

    # Stage B: required when pruning is enabled
    def totals(self) -> tuple[int, int]: ...  # (total_bytes, total_entries)
    def iter_lru(self) -> Iterable[tuple[str, int]]: ...  # (key, size_bytes), oldest first
    def delete_keys(self, keys: list[str]) -> None: ...

```

Method needs by stage:

- Stage A (`put`/`get` only): `ensure_schema`, `upsert_entry`, `touch_entry`.
- Stage B (LRU pruning enabled): add `totals`, `iter_lru`, `delete_keys`.

Methods intentionally removed from the protocol:

- `begin`: transaction handling remains internal to `IndexStore` implementation.
- `stats`: replaced by narrower `totals`.
- `list_entries` and `remove_missing_rows`: not part of this plan because DB consistency is assumed.

Rules:

- Storage and policies must not execute ad-hoc SQL directly.
- SQL statements are centralized in `IndexStore` for consistency and easier testing.
- Policies depend on typed `IndexStore` methods, not raw `sqlite3.Connection`.
- DB is treated as authoritative and consistent in this plan; no DB rebuild/reconciliation flow is included.

## Atomic Write Algorithm

For key `K`, final directory `E = root/K`.

1. Validate key and resolve paths.
2. Create temp dir `T = root/{key}.{uuid}.tmp` on same filesystem as `E` (keep `.tmp` as the final suffix).
3. Call custom writers in staging directory:

- `inputs_writer(T, *args, **kwargs)`
- `output_writer(T, output)`

4. Storage writes `T/metadata.json` atomically from `EntryMetadataModel.model_dump_json(...)`.
5. Acquire key-scoped write lock.
6. Commit:

- If `E` absent: `rename(T, E)`.
- If replace semantics enabled: stage old path swap (`E -> .old`) then `T -> E`, cleanup old.

7. In same operation window, update LRU index through `IndexStore.upsert_entry(...)`.
8. Release lock.
9. Trigger pruning if limits exceeded.

Failure handling:

- Any error before commit: delete `T`.
- `put` is successful only if both filesystem commit and `IndexStore.upsert_entry(...)` succeed.
- No automatic DB reconciliation/rebuild path is defined in this plan.

## Read and Touch Algorithm

1. Acquire key read lock.
2. Check existence/validity in global index DB (`IndexStore`) for key `K`.
3. Resolve `E` from key and call `output_reader(E)`.
4. Release read lock.
5. Update index `atime_ns` out-of-band via `IndexStore.touch_entry(...)`.

Important:

- No per-entry metadata rewrite on `get`.
- Touch path never acquires per-entry write lock for file mutation.
- `get` does not parse `metadata.json`; index DB is the authoritative source for entry presence/validity.

## Pruning Framework

### Trigger conditions

Pruning runs after successful `put` when the configured policy reports action is needed.

### Policy interface

```python
class PrunePolicy(Protocol):
    name: str

    def should_prune(
        self,
        *,
        index: IndexStore,
    ) -> bool:
        ...

    def select_victims(
        self,
        *,
        index: IndexStore,
    ) -> list[str]:  # keys to evict
        ...
```

Policy configuration ownership:

- Resource limits (for example `max_bytes`, `max_entries`) are constructor options of concrete policy classes, not `SyncFolderStorage`/`AsyncFolderStorage` options.
- Storage treats policy as a black box and only invokes `should_prune(...)` and `select_victims(...)`.

### LRU policy

- Concrete example: `LRUPrunePolicy(max_bytes: int | None = None, max_entries: int | None = None)`.
- Candidate order: ascending `atime_ns`.
- Evict oldest until both constraints are satisfied.
- Eviction transaction marks victims first, then filesystem deletion proceeds, then final DB cleanup.

### Eviction safety

1. Acquire prune lock (global).
2. Select victim keys via `PrunePolicy.select_victims(index=...)`.
3. For each victim key:

- Acquire key write lock.
- Delete entry folder atomically/safely.
- Remove index row.

4. Release locks.

## Concurrency Model

Locks:

- Per-key RW lock for read/write coordination.
- Global prune/index lock for policy pass and index schema maintenance.

Ordering rule to avoid deadlocks:

- Always acquire prune lock before any per-key lock during prune.
- Normal `get/put` paths should not hold prune lock.

## Testing Plan

1. Atomicity

- Writer interruption leaves no final partial entry.
- Temp directories are cleaned on failure.

2. Read touch behavior

- `get` updates DB `atime_ns`.
- `get` checks existence/validity via index DB only (no `metadata.json` parse on read path).
- `metadata.json` unchanged after repeated reads.

3. Metadata serialization/validation

- `put` writes `metadata.json` via Pydantic serialization.
- Corrupt or schema-invalid `metadata.json` is detected by maintenance/debug validation tools without affecting read path selection.

4. LRU correctness

- Oldest by `atime_ns` evicted first under policy-configured limits (for example `max_bytes` and `max_entries`).
- Recently touched entry survives when others are pruned.

5. Concurrency

- Parallel `get` calls do not block on metadata writes.
- Concurrent `put` and prune remain consistent.

## Open Decisions

1. Replace semantics for existing keys

- Strict no-overwrite (raise on existing key), or write-through replace with atomic swap.

2. Atime update mode

- Immediate synchronous DB update vs batched asynchronous updater.

3. Prune execution mode

- Inline in `put` vs background worker.

4. DB dependency boundary

- Use stdlib `sqlite3` only (preferred), no external DB deps.

## Acceptance Criteria

1. Reader/writer customization boundaries are enforced by API and tests.
2. Storage exclusively controls metadata writing.
3. Mutable access metadata is only in global DB.
4. Entry writes are atomic and crash-safe.
5. LRU pruning works from indexed metadata without full directory scans.
6. DB consistency is maintained by normal put/get/prune operations (no rebuild path).
