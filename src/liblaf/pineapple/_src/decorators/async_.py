from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import wrapt

from liblaf.pineapple._src.decorators.core import _resolve_key
from liblaf.pineapple._src.keying import validate_key
from liblaf.pineapple._src.storage.async_ import AsyncFolderStorage


def cache_async(
    fn: Callable[..., Awaitable[Any]] | None = None,
    *,
    storage: AsyncFolderStorage,
    key: Callable[..., str],
) -> (
    Callable[..., Awaitable[Any]]
    | Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]
):
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wrapt.decorator
        async def wrapper(
            wrapped: Callable[..., Awaitable[Any]],
            instance: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            del instance
            cache_key: str = validate_key(_resolve_key(key, args, kwargs))
            cached: Any | None = await storage.get(cache_key)
            if cached is not None:
                return cached
            output: Any = await wrapped(*args, **kwargs)
            await storage.put(cache_key, args=args, kwargs=kwargs, output=output)
            return output

        return wrapper(func)

    if fn is not None:
        return decorator(fn)
    return decorator


__all__ = ["cache_async"]
