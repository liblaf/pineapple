from __future__ import annotations

import pathlib
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager


def connect_sqlite(db_path: pathlib.Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


@contextmanager
def open_sqlite(db_path: pathlib.Path) -> Generator[sqlite3.Connection]:
    """Open a transaction-scoped SQLite connection and close it on exit."""
    conn = connect_sqlite(db_path)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


__all__ = ["connect_sqlite", "open_sqlite"]
