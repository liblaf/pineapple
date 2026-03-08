from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import wrapt

from liblaf.pineapple._src.decorators.core import _resolve_key
from liblaf.pineapple._src.keying import validate_key
from liblaf.pineapple._src.storage.async_ import AsyncFolderStorage
from liblaf.pineapple._src.storage.sync import SyncFolderStorage


def _resolve_sync_storage(
    *,
    storage: str | SyncFolderStorage,
    instance: Any,
) -> SyncFolderStorage:
    if isinstance(storage, SyncFolderStorage):
        return storage
    value: Any = getattr(instance, storage)
    if not isinstance(value, SyncFolderStorage):
        msg: str = f"{storage!r} is not a SyncFolderStorage"
        raise TypeError(msg)
    return value


def _resolve_async_storage(
    *,
    storage: str | AsyncFolderStorage,
    instance: Any,
) -> AsyncFolderStorage:
    if isinstance(storage, AsyncFolderStorage):
        return storage
    value: Any = getattr(instance, storage)
    if not isinstance(value, AsyncFolderStorage):
        msg: str = f"{storage!r} is not an AsyncFolderStorage"
        raise TypeError(msg)
    return value


def cache_method(
    *,
    storage: str | SyncFolderStorage,
    key: Callable[..., str],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wrapt.decorator
        def wrapper(
            wrapped: Callable[..., Any],
            instance: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if instance is None:
                msg: str = "cache_method requires a bound instance"
                raise TypeError(msg)
            target: SyncFolderStorage = _resolve_sync_storage(
                storage=storage,
                instance=instance,
            )
            key_args: tuple[Any, ...] = (instance, *args)
            cache_key: str = validate_key(_resolve_key(key, key_args, kwargs))
            cached: Any | None = target.get(cache_key)
            if cached is not None:
                return cached
            output: Any = wrapped(*args, **kwargs)
            target.put(cache_key, args=args, kwargs=kwargs, output=output)
            return output

        return wrapper(func)

    return decorator


def cache_method_async(
    *,
    storage: str | AsyncFolderStorage,
    key: Callable[..., str],
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wrapt.decorator
        async def wrapper(
            wrapped: Callable[..., Awaitable[Any]],
            instance: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if instance is None:
                msg: str = "cache_method_async requires a bound instance"
                raise TypeError(msg)
            target: AsyncFolderStorage = _resolve_async_storage(
                storage=storage,
                instance=instance,
            )
            key_args: tuple[Any, ...] = (instance, *args)
            cache_key: str = validate_key(_resolve_key(key, key_args, kwargs))
            cached: Any | None = await target.get(cache_key)
            if cached is not None:
                return cached
            output: Any = await wrapped(*args, **kwargs)
            await target.put(cache_key, args=args, kwargs=kwargs, output=output)
            return output

        return wrapper(func)

    return decorator


__all__ = ["cache_method", "cache_method_async"]
