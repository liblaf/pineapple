from __future__ import annotations

import pathlib

from liblaf.pineapple._src.storage.index.sqlite import connect_sqlite


def ensure_schema(db_path: pathlib.Path) -> None:
    with connect_sqlite(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                key TEXT PRIMARY KEY,
                size_bytes INTEGER NOT NULL,
                atime_ns INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_entries_atime ON entries(atime_ns)"
        )


__all__ = ["ensure_schema"]
