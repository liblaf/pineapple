from __future__ import annotations

from collections.abc import Callable
from typing import Any

import wrapt

from liblaf.pineapple._src.decorators.core import _resolve_key
from liblaf.pineapple._src.keying import validate_key
from liblaf.pineapple._src.storage.sync import SyncFolderStorage


def cache(
    fn: Callable[..., Any] | None = None,
    *,
    storage: SyncFolderStorage,
    key: Callable[..., str],
) -> Callable[..., Any] | Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wrapt.decorator
        def wrapper(
            wrapped: Callable[..., Any],
            instance: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            del instance
            cache_key: str = validate_key(_resolve_key(key, args, kwargs))
            cached: Any | None = storage.get(cache_key)
            if cached is not None:
                return cached
            output: Any = wrapped(*args, **kwargs)
            storage.put(cache_key, args=args, kwargs=kwargs, output=output)
            return output

        return wrapper(func)

    if fn is not None:
        return decorator(fn)
    return decorator


__all__ = ["cache"]
