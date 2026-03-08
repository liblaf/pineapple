# Plan 1: API Reset (Discussion-First)

Date: 2026-03-07
Status: In progress (initial implementation pass applied)

## Goal

Define a clean v1 API with no backward-compatibility constraints, emphasizing:

- storage-owned I/O customization,
- key-only decorator API,
- explicit user hashing helper,
- extensible metadata model.

## Proposed Direction

1. Storage owns custom I/O hooks

- `inputs_writer`, `output_reader`, `output_writer` are configured on storage objects.
- Decorators should not accept per-decorator reader/writer/input-writer overrides.
- This keeps behavior predictable per storage instance and reduces decorator complexity.

2. Expose only `key` in decorators

- Remove `hashkey` option entirely.
- Keep a single keying path: `key: Callable[..., str] | None`.

3. Public decorators use concrete defaults (not `None`-driven options)

- Exposed decorator APIs should default to concrete behavior (for example, default storage instance, default key strategy, default lock timeout), rather than relying on `None` placeholders.
- Keep `None` only where it semantically means "disabled" (for example, `ttl=None` means no expiration).
- Prefer deterministic runtime behavior without per-call fallback branching.

4. Provide `pineapple.hash(...)` helper

- Add stable short-hash helper for user-defined key strategies.
- Hashing implementation should use a stable cryptographic digest (for example, SHA-256; MD5 only if explicitly chosen for compatibility/perf tradeoffs).
- Typical replacement for old hashkey patterns:
  - `key=lambda *args, **kwargs: pineapple.hash(args)`
  - `key=lambda *args, **kwargs: pineapple.hash({"args": args, "kwargs": kwargs})`

5. No backward compatibility in v1 development

- Remove transitional aliases and compatibility-only paths.
- Prefer one canonical behavior over dual-mode support.

6. TTL integrated into metadata extensions

- TTL should be represented as metadata (`metadata["ttl"]`) and remain queryable via top-level `expires_at` only if needed by internal checks.
- Decorator-level metadata extension hooks remain first-class.

7. User metadata must be explicitly namespaced

- Library-defined metadata keys are reserved at top-level (for example: `key`, `created_at`, `updated_at`, `expires_at`, `status`, `hits`, `ttl`).
- User-defined metadata must live under a dedicated namespace key (proposed: `metadata["user"]`).
- User metadata is independent from library metadata and must not merge into library-managed fields.
- `metadata` should produce user payload only, stored in `metadata["user"]`.

## API Shape (Target)

1. Storage constructors (sync/async)

- Accept optional I/O hooks at initialization.
- Persist these as instance-level defaults used by `get/put/write_inputs`.

2. Decorator signatures

- Keep: `storage`, `key`, `ttl`, `metadata`, `lock_timeout`.
- Exposed defaults should be concrete values/instances in the public API (not `None` placeholders for standard behavior).
- Remove: `hashkey`, decorator-level `inputs_writer`, `output_reader`, `output_writer`.

3. Keying module

- Public helper: `pineapple.hash(value) -> str`.
- Default key generation uses same stable hash primitive.

## Discussion Checklist

1. Storage ownership semantics

- Do we allow runtime mutation of storage hooks after initialization, or keep them constructor-only?

2. `pineapple.hash` contract

- Exact truncation length and stability guarantees across versions.
- Expected behavior for optional dependencies (NumPy present/absent).

3. Metadata merge semantics

- Confirm merge semantics only within user metadata (`metadata["user"]`) if updates are incremental.
- Confirm namespacing rule for user metadata (always isolated under `metadata["user"]`, never merged into library keys).

4. Error model

- Decide whether key type validation should remain strict (`key` must return `str`) with immediate config errors.

5. Public export surface

- Confirm top-level exports for hash helper and storage classes.
- Confirm which codec helpers remain `_src` internal vs public.

## Validation Plan (before additional feature work)

1. API-level tests

- Decorators reject removed parameters.
- Decorators rely on storage-owned I/O hooks only.

2. Keying tests

- `pineapple.hash` deterministic behavior across representative payloads.

3. Storage hook tests

- Sync hooks receive `pathlib.Path`; async hooks receive `anyio.Path`.
- Hook usage verified through decorator calls.

4. Metadata/TTL tests

- TTL expiration works through extensible metadata path.
- Custom metadata merge behavior is deterministic.

## Out of Scope for Plan 1

- Performance optimization passes.
- Advanced eviction/indexing policies.
- Packaging/release hardening.

## Next Step

Complete validation and follow-up refactors, then freeze this plan.

## Implementation Snapshot (2026-03-07)

1. Completed in code

- Decorator APIs now expose concrete defaults for `storage`, `key`, and `metadata`.
- `hashkey` is absent from runtime source APIs (`src/`), keeping `key` as the only exposed keying option.
- `pineapple.hash(...)` is available and uses stable SHA-256 based hashing.
- User metadata is namespaced under `metadata["user"]` and no longer merged into library-managed top-level keys.
- Async input-writer contracts now use `anyio.Path`; sync contracts use `pathlib.Path`.

2. Remaining follow-ups

- Add explicit tests for metadata namespacing and reserved-key isolation behavior.
- Add hook contract tests for sync/async path object types.
- Decide whether to replace async lock acquire thread-offload with an async-compatible lock approach.
