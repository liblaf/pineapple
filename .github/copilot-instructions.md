# Project Guidelines

## Build and Test

- Install dependencies: `uv sync` (or `mise run install`).
- Run tests (preferred): `mise run test`.
- Run targeted tests while iterating: `pytest tests/unit/test_<name>.py`.
- Lint and format: `ruff format` then `ruff check --fix`.
- Type check: `pyright`.
- Build docs: `mkdocs build`.

## Architecture

- Public API is canonicalized in `src/liblaf/pineapple/__init__.py`.
- Key helpers are canonically exposed from `src/liblaf/pineapple/keys.py`.
- Everything under `src/liblaf/pineapple/_src/` is internal implementation namespace.
- Internal domains are split by responsibility:
  - `decorators/` decorator APIs and helper flows
  - `storage/` storage core + fs/metadata helpers
  - `io/` codecs (`load_*`/`save_*` naming)
  - `keying/` hash and key helpers
  - `shared/` shared types/ttl/path helpers

## Conventions

- Target Python is `>=3.13`.
- Keep files small and focused (target: <= 300 lines per module).
- Keep implementation out of `__init__.py`; use `__init__.py` for imports/re-exports.
- Preserve canonical export rules:
  - Do not add top-level exports casually.
  - If public export surface changes, update/validate `tests/unit/test_public_api_contract.py`.
- Keep `_src` private: internal re-exports there are allowed, but they are not public canonical API.
- Path typing/style:
  - Use `import pathlib` and annotate sync paths as `pathlib.Path`.
  - Use `anyio.Path` for async path surfaces.
  - Avoid `from pathlib import Path`.
- Public decorator API uses `metadata` (not `metadata_factory`) and does not expose `lock_timeout`.
- Prefer built-in/original exceptions over introducing custom wrapper exceptions.

## Workflow Notes

- Many files under `.config/` and CI workflow scaffolding are generated (`@generated`, `DO NOT EDIT`).
- Do not edit generated files unless explicitly requested.
- For behavior changes, run focused unit tests first, then broader test/lint/type checks.
