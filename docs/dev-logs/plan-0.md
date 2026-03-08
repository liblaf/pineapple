# Plan 0: Current Implementation Plan

Date: 2026-03-07
Scope: `liblaf/pineapple` internal cache core (`src/liblaf/pineapple/_src`)

## Current Architecture (Implemented)

1. Storage split is in place.

- `SyncFolderStorage` handles sync I/O paths.
- `AsyncFolderStorage` handles async I/O paths.

2. Async file operations use `anyio` APIs.

- Async storage and codec paths use `anyio.Path` / async file handles.
- No `aiofiles` usage.

3. Reader/writer path contracts are explicit.

- Sync reader/writer hooks use `pathlib.Path`.
- Async reader/writer hooks use `anyio.Path`.

4. Built-in output codec hooks are available.

- JSON: sync + async reader/writer helpers.
- NumPy: sync + async reader/writer helpers.
- Pickle: sync + async reader/writer helpers.
- Default output codec behavior reuses these helpers.

5. Inputs writer API matches decorated function signature.

- Inputs writer receives `(folder, *args, **kwargs)`.
- Default inputs writer persists `{"args": args, "kwargs": kwargs}`.

6. TTL now fits an extensible metadata system.

- Decorators support `metadata` hooks.
- TTL metadata is emitted under `metadata["ttl"]` and mirrored to top-level `expires_at` for compatibility.
- Storage `put(...)` supports metadata merge overlays.
- Expiration checks read either top-level `expires_at` or `metadata["ttl"]["expires_at"]`.

7. File-size refactor completed for oversized decorator module.

- Helper logic moved to `decorators_support.py`.
- `decorators.py` kept focused on decorator entrypoints.
- Internal files are now below the 300-line target.

## Immediate Next Steps

1. Add tests for metadata extensibility + TTL compatibility.

- Confirm expiration works with both top-level and nested TTL metadata.
- Validate `metadata` merge behavior for sync and async decorators.

2. Add tests for hook path-type contracts.

- Sync hooks receive `pathlib.Path`.
- Async hooks receive `anyio.Path`.

3. Add tests for inputs writer argument passthrough.

- Ensure custom inputs writers see original `*args, **kwargs` for all decorator variants.

4. Add tests for built-in codec helper functions.

- JSON/NumPy/Pickle helper read-write roundtrip coverage (sync + async).
- NumPy-missing behavior coverage.

5. Review public exports and docs.

- Decide which codec helpers should be public top-level exports vs `_src` only.
- Document recommended usage patterns for custom `inputs_writer`, `output_reader`, `output_writer`, and `metadata`.

## Risks / Follow-ups

1. Metadata merge policy is shallow.

- Current `metadata.update(custom)` behavior can overwrite nested objects.
- Consider optional deep-merge strategy if needed.

2. Async lock acquire currently uses thread offload.

- File lock API is sync; this is acceptable for now, but can be revisited if contention profiling shows issues.

3. Optional dependency behavior (NumPy) should stay explicit.

- Keep deterministic errors and tests when NumPy is unavailable.
