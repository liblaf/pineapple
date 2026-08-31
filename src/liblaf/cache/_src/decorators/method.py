from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import wrapt

from liblaf.cache._src.decorators.core import _resolve_key
from liblaf.cache._src.keying import validate_key
from liblaf.cache._src.storage.async_ import AsyncFolderStorage
from liblaf.cache._src.storage.sync import SyncFolderStorage


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
    """Cache an instance method through a storage object or attribute.

    Args:
        storage: `SyncFolderStorage` or name of an instance attribute holding
            one.
        key: Callable receiving the instance followed by method arguments.

    Returns:
        A decorator for a bound synchronous instance method.
    """

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
            with target.lock(cache_key):
                if target.contains(cache_key):
                    return target.get(cache_key)
                output: Any = wrapped(*args, **kwargs)
                target.put(cache_key, args=args, kwargs=kwargs, output=output)
            target.prune()
            return output

        return wrapper(func)

    return decorator


def cache_method_async(
    *,
    storage: str | AsyncFolderStorage,
    key: Callable[..., str],
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """Cache an awaitable instance method through async storage.

    Args:
        storage: `AsyncFolderStorage` or name of an instance attribute holding
            one.
        key: Callable receiving the instance followed by method arguments.

    Returns:
        A decorator for a bound awaitable instance method.
    """

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
            async with target.lock(cache_key):
                if await target.contains(cache_key):
                    return await target.get(cache_key)
                output: Any = await wrapped(*args, **kwargs)
                await target.put(cache_key, args=args, kwargs=kwargs, output=output)
            await target.prune()
            return output

        return wrapper(func)

    return decorator


__all__ = ["cache_method", "cache_method_async"]
