from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, overload

import joblib
import platformdirs
import wrapt

from liblaf.cache._src.decorators.core import _resolve_key
from liblaf.cache._src.keying import validate_key
from liblaf.cache._src.shared import (
    AsyncInputsWriter,
    AsyncOutputReader,
    AsyncOutputWriter,
)
from liblaf.cache._src.storage.async_ import AsyncFolderStorage
from liblaf.cache._src.storage.policies import PrunePolicy


@overload
def cache_async[**P, R](
    fn: Callable[P, Awaitable[R]],
    *,
    storage: AsyncFolderStorage | None = None,
    key: Callable[..., str] | None = None,
    inputs_writer: AsyncInputsWriter | None = None,
    output_writer: AsyncOutputWriter | None = None,
    output_reader: AsyncOutputReader[Any] | None = None,
    purge: PrunePolicy | None = None,
) -> Callable[P, Awaitable[R]]: ...


@overload
def cache_async[**P, R](
    fn: None = None,
    *,
    storage: AsyncFolderStorage | None = None,
    key: Callable[..., str] | None = None,
    inputs_writer: AsyncInputsWriter | None = None,
    output_writer: AsyncOutputWriter | None = None,
    output_reader: AsyncOutputReader[Any] | None = None,
    purge: PrunePolicy | None = None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]: ...


def cache_async(
    fn: Callable[..., Awaitable[Any]] | None = None,
    *,
    storage: AsyncFolderStorage | None = None,
    key: Callable[..., str] | None = None,
    inputs_writer: AsyncInputsWriter | None = None,
    output_writer: AsyncOutputWriter | None = None,
    output_reader: AsyncOutputReader[Any] | None = None,
    purge: PrunePolicy | None = None,
) -> (
    Callable[..., Awaitable[Any]]
    | Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]
):
    """Cache an awaitable function result in a local directory tree.

    The async wrapper has the same publication and single-flight contract as
    [`cache`][liblaf.cache.cache], while its codec hooks use `anyio.Path`.

    Args:
        fn: Awaitable function to decorate, when used as `@cache_async`.
        storage: Existing async storage owner.
        key: Callable returning a non-empty string key.
        inputs_writer: Optional one-decorator async inputs writer.
        output_writer: Optional one-decorator async output writer.
        output_reader: Optional one-decorator async output reader.
        purge: Optional policy for a newly-created storage.

    Returns:
        The wrapped awaitable function, or a decorator with keyword options.
    """

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        custom_storage = any(
            option is not None
            for option in (inputs_writer, output_writer, output_reader, purge)
        )
        if storage is not None and custom_storage:
            message = "storage cannot be combined with writer, reader, or purge options"
            raise TypeError(message)
        target = (
            storage
            if storage is not None
            else AsyncFolderStorage(
                Path(platformdirs.user_cache_dir("liblaf-cache")),
                inputs_writer=inputs_writer,
                output_writer=output_writer,
                output_reader=output_reader,
                prune_policy=purge,
            )
        )
        key_builder = (
            (
                lambda *args, **kwargs: joblib.hash(
                    (
                        getattr(func, "__module__", type(func).__module__),
                        getattr(func, "__qualname__", type(func).__qualname__),
                        args,
                        kwargs,
                    )
                )
            )
            if key is None
            else key
        )

        @wrapt.decorator
        async def wrapper(
            wrapped: Callable[..., Awaitable[Any]],
            instance: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            del instance
            cache_key: str = validate_key(_resolve_key(key_builder, args, kwargs))
            async with target.lock(cache_key):
                if await target.contains(cache_key):
                    return await target.get(cache_key)
                output: Any = await wrapped(*args, **kwargs)
                await target.put(cache_key, args=args, kwargs=kwargs, output=output)
            await target.prune()
            return output

        return wrapper(func)

    if fn is not None:
        return decorator(fn)
    return decorator


__all__ = ["cache_async"]
