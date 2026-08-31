"""Small dict-like interfaces over directory-backed cache entries."""

from __future__ import annotations

from collections.abc import Iterator, MutableMapping
from pathlib import Path
from typing import Any

from ._src.storage import AsyncFolderStorage, SyncFolderStorage
from .keys import validate_key


class Cache(MutableMapping[str, Any]):
    """A synchronous mapping over inspectable cache entry directories.

    Args:
        path: Root directory for this mapping's entries and index.
        **kwargs: Options accepted by [`SyncFolderStorage`][liblaf.cache.SyncFolderStorage].

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     values = Cache(directory)
        ...     values["answer"] = 42
        ...     values["answer"]
        42
    """

    def __init__(self, path: str | Path, **kwargs: Any) -> None:
        self.storage = SyncFolderStorage(path, **kwargs)

    def __getitem__(self, key: str) -> Any:
        if not self.storage.contains(validate_key(key)):
            raise KeyError(key)
        return self.storage.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.storage.put(validate_key(key), args=(), kwargs={}, output=value)

    def __delitem__(self, key: str) -> None:
        if not self.storage.contains(validate_key(key)):
            raise KeyError(key)
        self.storage.delete(key)

    def __iter__(self) -> Iterator[str]:
        yield from self.storage.keys()

    def __len__(self) -> int:
        return len(self.storage)


class AsyncCache:
    """Awaitable counterpart to [`Cache`][liblaf.cache.Cache].

    Python's `Mapping` protocol is synchronous, so this type exposes explicit
    `await get()`, `await set()`, and `await delete()` methods instead.

    Args:
        path: Root directory for this mapping's entries and index.
        **kwargs: Options accepted by [`AsyncFolderStorage`][liblaf.cache.AsyncFolderStorage].
    """

    def __init__(self, path: str | Path, **kwargs: Any) -> None:
        self.storage = AsyncFolderStorage(path, **kwargs)

    async def get(self, key: str) -> Any:
        if not await self.storage.contains(validate_key(key)):
            raise KeyError(key)
        return await self.storage.get(key)

    async def set(self, key: str, value: Any) -> None:
        await self.storage.put(validate_key(key), args=(), kwargs={}, output=value)

    async def delete(self, key: str) -> None:
        if not await self.storage.contains(validate_key(key)):
            raise KeyError(key)
        await self.storage.delete(key)


__all__ = ["AsyncCache", "Cache"]
