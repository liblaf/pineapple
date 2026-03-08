# Plan 2: Structural Refactor and Stabilization

Date: 2026-03-07
Status: Proposed
Scope: whole repository (`src`, docs, tests)

## Why Plan 2

Current code is functional but has accumulated structural debt during rapid API iteration. The main concerns are module size, duplication, and drift between implementation and planning docs.

This library is in early development; backward compatibility and migration support are not required in this plan.

## Review Findings (Codebase-Wide)

1. Oversized core modules are reducing maintainability.

- `src/liblaf/pineapple/_src/decorators.py` is 465 lines.
- `src/liblaf/pineapple/_src/storage.py` is 381 lines.
- These exceed the previously stated target of <= 300 lines and make review/change safety worse.

2. Sync/async logic duplication is high in critical paths.

- Decorator logic is repeated across `cache`, `cache_async`, `cache_method`, `cache_method_async`.
- Storage logic is repeated across `SyncFolderStorage` and `AsyncFolderStorage` for metadata handling, lifecycle, and clear/delete semantics.
- Codec fallback logic is repeated between sync and async pathways.

3. Public API/exceptions are inconsistent with execution behavior.

- Historical docs still mention custom exception classes and timeout-specific behavior.
- Execution policy for this version is built-in/original exceptions only, with blocking lock acquisition by default.

4. Dead/unused code exists in hot modules.

- `_DEFAULT_SYNC_STORAGE` and `_DEFAULT_ASYNC_STORAGE` in `src/liblaf/pineapple/_src/decorators_support.py` are not used.
- `write_inputs` methods in storage classes appear unused by current decorators.

5. Side effects are mixed into read-style methods.

- `contains(...)` may delete expired entries.
- `get(...)` also checks expiration and mutates metadata (`hits`, `last_accessed_at`).
- This is workable but should be explicitly documented and split into clearer internal primitives.

6. Test coverage scaffolding is missing.

- No `tests/` files are currently present even though strict pytest config exists in `pyproject.toml`.
- Refactors are therefore high-risk without regression safety nets.

7. Documentation drift is visible.

- `docs/dev-logs/plan-0.md` claims all modules are under 300 lines and mentions outdated async lock behavior.
- Current implementation has moved forward (read/write lock model, wrapt, `metadata` argument naming) but docs do not consistently reflect that.

## Refactor Objectives

1. Bring module size and cohesion under control.
2. Reduce sync/async duplication while keeping explicit type-safe APIs.
3. Enforce a single canonical location per public object.
4. Keep private internals private by naming and export policy.
5. Make exported API reflect actual behavior (especially exceptions).
6. Reintroduce confidence via focused tests before and during refactor.
7. Prioritize internal clarity and correctness over compatibility with previous unstable API shapes.
8. Ensure decorators preserve wrapped callable typing/signature (`P`, `T`) across sync/async and method variants.
9. Provide a public `keys` module with practical key helpers for function and method decorators.
10. Do not use custom exception classes; raise original exceptions as-is or built-in exceptions (`ValueError`, `TypeError`, etc.).
11. Do not expose timeout parameters in public decorators in this version; lock acquisition is blocking by default.
12. Use `metadata` as the public decorator argument name (not `metadata_factory`).

## Exposure and Privacy Rules (Mandatory)

1. Single canonical public location.

- Every public object must have exactly one canonical import path.
- No duplicated public re-exports across canonical public modules.
- Top-level package (`liblaf.pineapple`) should only expose the approved public surface.
- Key helpers (`hashkey`, `method_key`) are canonically exposed from `liblaf.pineapple.keys`.
- Internal `_src` re-exports are allowed for private convenience, but they do not define canonical public import paths.

2. Private object policy.

- Private modules are private by namespace when located under `liblaf.pineapple._src.*`; module filenames there do not require a leading `_`.
- Private functions, classes, methods, and constants must start with `_`.
- Any non-`_` symbol is considered public-candidate and must not be exposed at top-level unless explicitly approved as public API.
- Internal helper modules should remain under internal namespace and never be top-level exports.

3. Export gatekeeping.

- All top-level exports must be explicitly listed and reviewed.
- Add tests that fail when new top-level exports appear without intentional registration.

## Public API Catalog (Canonical)

All public APIs must come from exactly one canonical import path listed below.

1. Canonical module: `liblaf.pineapple`

- `cache`
- `cache_async`
- `cache_method`
- `cache_method_async`
- `SyncFolderStorage`
- `AsyncFolderStorage`
- `hash`

2. Canonical module: `liblaf.pineapple.keys`

- `hashkey`
- `method_key` (must exclude first positional arg: `self`/`cls`)

3. Non-public by policy

- Everything under `liblaf.pineapple._src.*` is internal implementation namespace.
- No `_src` module may be treated as an additional canonical public location.

## Public API Reference (Detailed Prototypes)

This section is the implementation-facing contract for the canonical public API.

1. Module `liblaf.pineapple`: decorators and core storage types.

```python
from collections.abc import Awaitable, Callable
import os
from typing import Any

def cache[**P, T](
  fn: Callable[P, T] | None = None,
  *,
  storage: SyncFolderStorage | None = None,
  key: KeyFunc = default_key,
  ttl: TTLValue | TtlFunc | None = None,
  metadata: Callable[[tuple[Any, ...], dict[str, Any], T], dict[str, Any] | None] = ...,
) -> Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]]: ...

def cache_async[**P, T](
  fn: Callable[P, Awaitable[T]] | None = None,
  *,
  storage: AsyncFolderStorage | None = None,
  key: KeyFunc = default_key,
  ttl: TTLValue | TtlFunc | None = None,
  metadata: Callable[[tuple[Any, ...], dict[str, Any], T], dict[str, Any] | None] = ...,
) -> Callable[P, Awaitable[T]] | Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]: ...

def cache_method[**P, T](
  fn: Callable[P, T] | None = None,
  *,
  storage: str | SyncFolderStorage,
  key: MethodKeyFunc = default_key,
  ttl: TTLValue | MethodTtlFunc | None = None,
  metadata: Callable[[tuple[Any, ...], dict[str, Any], T], dict[str, Any] | None] = ...,
) -> Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]]: ...

def cache_method_async[**P, T](
  fn: Callable[P, Awaitable[T]] | None = None,
  *,
  storage: str | AsyncFolderStorage,
  key: MethodKeyFunc = default_key,
  ttl: TTLValue | MethodTtlFunc | None = None,
  metadata: Callable[[tuple[Any, ...], dict[str, Any], T], dict[str, Any] | None] = ...,
) -> Callable[P, Awaitable[T]] | Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]: ...

def hash(value: Any) -> str: ...
```

Decorator argument semantics:

- `fn`: optional; if omitted, return a decorator factory (`functools.partial` behavior).
- `storage`: for `cache`/`cache_async`, optional concrete storage instance; if omitted, resolve per-callable default storage.
- `storage` in method decorators: required and explicit (`str` attribute name on instance or concrete storage object).
- `key`: must return `str`; method decorators pass `(instance, *args)` into key resolution.
- `ttl`: `None`, fixed TTL value, or callable TTL resolver.
- `metadata`: receives only `(args, kwargs, result)` and returns user metadata payload.
- Lock acquisition is blocking by default in this version; timeout parameters are intentionally not exposed.

2. Module `liblaf.pineapple`: storage class public methods.

```python
import os
import anyio
from pathlib import Path
from typing import Any, Self

class SyncFolderStorage:
  def __init__(
    self,
    path: str | os.PathLike[str],
    *,
    inputs_writer: InputsWriter | None = None,
    output_reader: OutputReader[Any] | None = None,
    output_writer: OutputWriter[Any] | None = None,
  ) -> None: ...

  @classmethod
  def user_cache(cls, path: str | os.PathLike[str], **kwargs: Any) -> Self: ...
  @classmethod
  def relative(cls, path: str | os.PathLike[str], **kwargs: Any) -> Self: ...
  @classmethod
  def absolute(cls, path: str | os.PathLike[str], **kwargs: Any) -> Self: ...

  @property
  def root_dir(self) -> Path: ...

  def entry_dir(self, key: str) -> Path: ...
  def lock_path(self, key: str) -> Path: ...
  def contains(self, key: str) -> bool: ...
  def get(self, key: str) -> Any: ...  # raises KeyError if missing/expired
  def put(
    self,
    key: str,
    *,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    output: Any,
    user_metadata: dict[str, Any] | None = None,
    library_metadata: EntryMetadataPatch | dict[str, Any] | None = None,
  ) -> None: ...
  def write_inputs(self, key: str, *args: Any, **kwargs: Any) -> None: ...
  def delete(self, key: str) -> None: ...
  def clear(self) -> None: ...


class AsyncFolderStorage:
  def __init__(
    self,
    path: str | os.PathLike[str],
    *,
    inputs_writer: AsyncInputsWriter | None = None,
    output_reader: AsyncOutputReader[Any] | None = None,
    output_writer: AsyncOutputWriter[Any] | None = None,
  ) -> None: ...

  @classmethod
  def user_cache(cls, path: str | os.PathLike[str], **kwargs: Any) -> Self: ...
  @classmethod
  def relative(cls, path: str | os.PathLike[str], **kwargs: Any) -> Self: ...
  @classmethod
  def absolute(cls, path: str | os.PathLike[str], **kwargs: Any) -> Self: ...

  @property
  def root_dir(self) -> anyio.Path: ...

  def entry_dir(self, key: str) -> anyio.Path: ...
  def lock_path(self, key: str) -> anyio.Path: ...
  async def contains(self, key: str) -> bool: ...
  async def get(self, key: str) -> Any: ...  # raises KeyError if missing/expired
  async def put(
    self,
    key: str,
    *,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    output: Any,
    user_metadata: dict[str, Any] | None = None,
    library_metadata: EntryMetadataPatch | dict[str, Any] | None = None,
  ) -> None: ...
  async def write_inputs(self, key: str, *args: Any, **kwargs: Any) -> None: ...
  async def delete(self, key: str) -> None: ...
  async def clear(self) -> None: ...
```

Storage argument semantics:

- Constructor policy: `__init__` accepts only `path` and reader/writer hooks.
- `path` in `__init__`: resolved with default user-cache root.
- Root selection helpers: `user_cache(...)`, `relative(...)`, and `absolute(...)`.
- `relative(path, ...)`: convenience constructor for paths resolved relative to current working directory.
- Naming policy: prefer `relative` over `cwd` in public API because it reads better at call sites; no migration alias is required in this early stage.
- Directory creation policy: storage root/entry folders are created lazily on first write or lock-path use; constructors do not eagerly create directories.
- Async path policy: all async storage path surfaces use `anyio.Path` (no `pathlib.Path` in async APIs).
- `inputs_writer`, `output_reader`, `output_writer`: optional codec/hooks configured per storage instance.
- `key` parameters: validated safe relative entry keys.
- `get(key)`: raises `KeyError` when entry is missing or expired.
- `put(...)`: requires explicit `args`, `kwargs`, and `output`; optional `user_metadata` and library metadata patch.
- `contains(key)`: may perform expiry cleanup as part of existence checks.

3. Module `liblaf.pineapple.keys`: canonical key helper API.

```python
from typing import Any

def hashkey(*args: Any, **kwargs: Any) -> str: ...
def method_key(*args: Any, **kwargs: Any) -> str: ...  # excludes first positional arg from hashing
```

4. Public error contract.

- Do not expose or raise project-defined custom exception classes.
- Raise built-in exceptions for validation/contract violations (`ValueError`, `TypeError`, `KeyError`).
- Propagate third-party/library exceptions as-is (for example lock timeout errors).

## Proposed Architecture Changes

### Target Source Layout (Grouped)

```text
src/liblaf/pineapple/
  __init__.py                        # single public export surface
  keys.py                            # canonical public key helpers (hashkey, method_key)
  _src/
    __init__.py
    decorators/
      __init__.py                    # optional internal aggregation only
      decorators.py                  # public decorator entrypoints (small)
      decorators_core.py             # common cache orchestration helpers
      decorators_sync.py             # sync adapters
      decorators_async.py            # async adapters
      decorators_support.py          # callable-id/default-storage resolution helpers
    storage/
      __init__.py
      core.py                        # SyncFolderStorage / AsyncFolderStorage API shells
      metadata.py                    # metadata read/write/merge helpers
      fs_sync.py                     # sync fs lifecycle ops
      fs_async.py                    # async fs lifecycle ops
    io/
      __init__.py
      codecs.py                      # codec function surface for internal use
      json.py                        # json codec details
      numpy.py                       # numpy codec details
      pickle.py                      # pickle codec details
      default.py                     # fallback selection logic
    shared/
      __init__.py
      types.py
      ttl.py
      paths.py
    keying/
      __init__.py
      hash.py
      keys.py                        # internal key helper implementation
```

### Mapping From Current Files

1. `src/liblaf/pineapple/_src/decorators.py` -> `src/liblaf/pineapple/_src/decorators/decorators.py`
2. `src/liblaf/pineapple/_src/storage.py` -> `src/liblaf/pineapple/_src/storage/core.py` + `src/liblaf/pineapple/_src/storage/metadata.py` + `src/liblaf/pineapple/_src/storage/fs_sync.py` + `src/liblaf/pineapple/_src/storage/fs_async.py`
3. `src/liblaf/pineapple/_src/codecs.py` -> `src/liblaf/pineapple/_src/io/codecs.py` + codec family modules
4. `src/liblaf/pineapple/_src/keying.py` -> `src/liblaf/pineapple/_src/keying/hash.py` + `src/liblaf/pineapple/_src/keying/keys.py`
5. `src/liblaf/pineapple/_src/{types.py,ttl.py,paths.py}` -> `src/liblaf/pineapple/_src/shared/`
6. `src/liblaf/pineapple/_src/decorators_support.py` -> `src/liblaf/pineapple/_src/decorators/decorators_support.py`
7. New public facade: `src/liblaf/pineapple/keys.py` -> thin canonical export module for key helpers.

### Grouping Rules

1. Use domain packages under `src/liblaf/pineapple/_src/` (`decorators`, `storage`, `io`, `shared`, `keying`) rather than one large flat folder.
2. Public object definitions can live in grouped `_src` modules, but each public object has exactly one canonical exposure location in the documented export map (for example `src/liblaf/pineapple/__init__.py` for core API, `src/liblaf/pineapple/keys.py` for key helpers).
3. Modules inside `_src` do not need `_` filename prefixes; privacy is established by `_src` namespace and top-level export policy.
4. Keep depth shallow: at most two layers under `_src`.
5. Keep each module focused and under 300 lines where practical.

6. Decorator decomposition.

- Keep implementation entrypoints in `src/liblaf/pineapple/_src/decorators/decorators.py` only.
- Keep canonical public exposure for decorator symbols at `src/liblaf/pineapple/__init__.py`.
- Move shared lock + read-through + write-through flow into internal helpers:
  - `src/liblaf/pineapple/_src/decorators/decorators_core.py` for common cache orchestration.
  - `src/liblaf/pineapple/_src/decorators/decorators_sync.py` and `src/liblaf/pineapple/_src/decorators/decorators_async.py` for minimal mode-specific adapters.
- Keep wrapt and overload signatures in public module; move implementation details out.

2. Storage decomposition.

- Split metadata and file lifecycle helpers from class definitions:
  - `src/liblaf/pineapple/_src/storage/metadata.py` for metadata read/write/merge/expiry utilities.
  - `src/liblaf/pineapple/_src/storage/fs_sync.py` and `src/liblaf/pineapple/_src/storage/fs_async.py` for filesystem operations.
- Keep class APIs in `src/liblaf/pineapple/_src/storage/core.py` but delegate to small helpers.

3. Codec decomposition.

- Extract codec families into separate modules:
  - `src/liblaf/pineapple/_src/io/json.py`, `src/liblaf/pineapple/_src/io/numpy.py`, `src/liblaf/pineapple/_src/io/pickle.py`, `src/liblaf/pineapple/_src/io/default.py`.
- Keep external behavior unchanged; naming may be normalized for consistency (for example `load_*` / `save_*`) when fully propagated through `src/liblaf/pineapple/_src/io/codecs.py`.

4. Key helper surface.

- Add `src/liblaf/pineapple/_src/keying/keys.py` with:
  - `hashkey(*args, **kwargs) -> str`: stable hash-based key helper for regular callables.
  - `method_key(*args, **kwargs) -> str`: method helper that excludes the first positional arg (`self`/`cls`) from key hashing.
- Expose canonical public API from `src/liblaf/pineapple/keys.py` only.
- Keep behavior deterministic and aligned with the same hash primitive used by `hash`/`default_key`.

5. Exception policy cleanup.

- Remove custom exception classes and their exports.
- Use built-in exceptions for argument/configuration validation (`ValueError`, `TypeError`) and let external/library exceptions propagate unchanged.
- Define and document canonical import location for each remaining public symbol.

6. Internal API hygiene.

- Remove unused globals and methods (or add intended call sites/tests if keeping them).
- Add explicit private helpers for:
  - existence check without mutation,
  - expiration cleanup,
  - access-touch updates.

## Execution Plan

### Phase 1 - Safety Net First

1. Create baseline test suite (must pass before refactor).

- Decorator behavior: hit/miss, sync/async parity, method/non-method parity.
- Decorator typing behavior: wrapped function signature is preserved by type checker for all decorator variants.
- Lock behavior: verify no public timeout parameter is exposed and lock paths are blocking by default.
- Exception policy: verify no custom project-defined exception classes are raised by shared paths.
- Decorator API naming: verify public decorator parameter name is `metadata`.
- Metadata behavior: user metadata namespacing and TTL library metadata.
- Storage behavior: `contains/get/delete/clear` and expiration semantics.

2. Add smoke tests for keying and default codecs.

- Deterministic hashing.
- JSON/NumPy/Pickle fallback selection.
- `hashkey` and `method_key` deterministic behavior and collision-sanity checks.
- `method_key` excludes first positional argument from hash input.

3. Add export-contract tests.

- Assert exported symbols match the `Public API Catalog (Canonical)` exactly.
- Assert each public symbol has one canonical location only.
- Assert `hashkey` and `method_key` are canonically exposed from `liblaf.pineapple.keys`.
- Assert private symbols (`_`-prefixed functions/classes/methods/constants) are not top-level exports.
- Assert modules under `liblaf.pineapple._src.*` are not treated as additional canonical public locations.

Acceptance:

- New tests exist and pass locally.
- Baseline behavior captured before structural edits.
- Export/privacy contract tests pass.

### Phase 2 - Decorators Refactor

1. Extract orchestration internals from `src/liblaf/pineapple/_src/decorators/decorators.py`.
2. Preserve exact public signatures and overloads.
3. Keep method decorators API parity with function decorators (`fn=None` -> partial).
4. Preserve wrapped callable typing (`P`, `T`) and method typing behavior through wrappers.

Acceptance:

- `src/liblaf/pineapple/_src/decorators/decorators.py` <= 280 lines.
- No public signature changes.
- Type-checking confirms decorated callables keep original callable signatures/return types.
- Existing/new tests pass.

### Phase 3 - Storage Refactor

1. Extract metadata and fs internals into helper modules.
2. Normalize expiration and mutation flow with clear helper boundaries.
3. Keep on-disk schema unchanged.

Acceptance:

- `src/liblaf/pineapple/_src/storage/core.py` <= 280 lines.
- All storage tests pass unchanged.

### Phase 4 - Codec Refactor

1. Split codec families into focused files.
2. Re-export existing helper names from `codecs.py`.

Acceptance:

- `codecs.py` becomes orchestration-only index.
- Codec behavior/tests unchanged.

### Phase 5 - Public Surface and Docs Alignment

1. Remove custom exception classes/exports and align all call sites with built-in/original exceptions.
2. Remove stale/unused symbols.
3. Apply canonical-export map and private naming policy.
4. Update docs:

- `docs/plan.md`
- `docs/dev-logs/plan-0.md`
- `docs/dev-logs/plan-1.md`

Acceptance:

- Docs match code behavior.
- No stale exported symbols without implementation meaning.
- Each public object has exactly one canonical import location.
- Private symbols are `_`-prefixed and are not top-level exported.
- `_src` modules are internal implementation namespace and not additional canonical public surface.

## Risk Management

1. Behavior drift during decomposition.

- Mitigation: tests first, move-only commits, no logic rewrites during extraction.

2. Typing regressions with PEP 695 + wrapt overloads.

- Mitigation: run pyright after each phase and keep overload tests/examples.

3. Async parity regressions.

- Mitigation: mirrored sync/async tests for each feature path.

## Deliverables

1. Refactored module layout with smaller focused files.
2. Restored test suite with coverage for core behavior.
3. Updated planning/docs matching actual architecture.
4. Cleaned public API surface with explicit exception policy.

## Immediate Next Actions

1. Create `tests/unit/test_decorators_sync.py` and `tests/unit/test_decorators_async.py`.
2. Create `tests/unit/test_storage_sync.py` and `tests/unit/test_storage_async.py`.
3. Lock in current behavior snapshots before module extraction.
4. Start Phase 2 extraction of decorator internals.
