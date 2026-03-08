from __future__ import annotations

import pathlib
from collections.abc import Iterable

from liblaf.pineapple._src.storage.index.schema import ensure_schema
from liblaf.pineapple._src.storage.index.sqlite import connect_sqlite


class IndexStore:
    def __init__(self, db_path: pathlib.Path) -> None:
        self._db_path = db_path

    def ensure_schema(self) -> None:
        ensure_schema(self._db_path)

    def upsert_entry(self, *, key: str, size_bytes: int, atime_ns: int) -> None:
        with connect_sqlite(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO entries(key, size_bytes, atime_ns)
                VALUES(?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    size_bytes = excluded.size_bytes,
                    atime_ns = excluded.atime_ns
                """,
                (key, size_bytes, atime_ns),
            )

    def touch_entry(self, *, key: str, atime_ns: int) -> None:
        with connect_sqlite(self._db_path) as conn:
            conn.execute(
                "UPDATE entries SET atime_ns = ? WHERE key = ?", (atime_ns, key)
            )

    def has_entry(self, *, key: str) -> bool:
        with connect_sqlite(self._db_path) as conn:
            row = conn.execute("SELECT 1 FROM entries WHERE key = ?", (key,)).fetchone()
        return row is not None

    def totals(self) -> tuple[int, int]:
        with connect_sqlite(self._db_path) as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(size_bytes), 0), COUNT(*) FROM entries"
            ).fetchone()
        if row is None:
            return (0, 0)
        return (int(row[0]), int(row[1]))

    def iter_lru(self) -> Iterable[tuple[str, int]]:
        with connect_sqlite(self._db_path) as conn:
            rows = conn.execute(
                "SELECT key, size_bytes FROM entries ORDER BY atime_ns ASC"
            ).fetchall()
        return [(str(key), int(size_bytes)) for key, size_bytes in rows]

    def delete_keys(self, keys: list[str]) -> None:
        if not keys:
            return
        with connect_sqlite(self._db_path) as conn:
            conn.executemany(
                "DELETE FROM entries WHERE key = ?", [(key,) for key in keys]
            )


__all__ = ["IndexStore"]
