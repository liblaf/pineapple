from __future__ import annotations

import threading

import anyio


class KeyLockPool:
    def __init__(self) -> None:
        self._guard = threading.Lock()
        self._locks: dict[str, threading.Lock] = {}

    def get(self, key: str) -> threading.Lock:
        with self._guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = threading.Lock()
                self._locks[key] = lock
            return lock


class AsyncKeyLockPool:
    def __init__(self) -> None:
        self._guard = anyio.Lock()
        self._locks: dict[str, anyio.Lock] = {}

    async def get(self, key: str) -> anyio.Lock:
        async with self._guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = anyio.Lock()
                self._locks[key] = lock
            return lock


__all__ = ["AsyncKeyLockPool", "KeyLockPool"]
