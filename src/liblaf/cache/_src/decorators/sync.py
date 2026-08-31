from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, overload

import joblib
import platformdirs
import wrapt

from liblaf.cache._src.decorators.core import _resolve_key
from liblaf.cache._src.keying import validate_key
from liblaf.cache._src.shared import OutputReader, SyncInputsWriter, SyncOutputWriter
from liblaf.cache._src.storage.policies import PrunePolicy
from liblaf.cache._src.storage.sync import SyncFolderStorage


@overload
def cache[**P, R](
    fn: Callable[P, R],
    *,
    storage: SyncFolderStorage | None = None,
    key: Callable[..., str] | None = None,
    inputs_writer: SyncInputsWriter | None = None,
    output_writer: SyncOutputWriter | None = None,
    output_reader: OutputReader[Any] | None = None,
    purge: PrunePolicy | None = None,
) -> Callable[P, R]: ...


@overload
def cache[**P, R](
    fn: None = None,
    *,
    storage: SyncFolderStorage | None = None,
    key: Callable[..., str] | None = None,
    inputs_writer: SyncInputsWriter | None = None,
    output_writer: SyncOutputWriter | None = None,
    output_reader: OutputReader[Any] | None = None,
    purge: PrunePolicy | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def cache(
    fn: Callable[..., Any] | None = None,
    *,
    storage: SyncFolderStorage | None = None,
    key: Callable[..., str] | None = None,
    inputs_writer: SyncInputsWriter | None = None,
    output_writer: SyncOutputWriter | None = None,
    output_reader: OutputReader[Any] | None = None,
    purge: PrunePolicy | None = None,
) -> Callable[..., Any] | Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Cache a synchronous function result in a local directory tree.

    The wrapper takes the per-key filesystem lock, re-checks the cache, then
    publishes a successful result atomically. It is single-flight for live
    owners, not exactly-once for external side effects.

    Args:
        fn: Function to decorate, when used as `@cache`.
        storage: Existing storage owner. It cannot be combined with codec or
            purge options.
        key: Callable returning a non-empty string key. Omit it for a
            function-identity and argument key derived with `joblib.hash`.
        inputs_writer: Optional one-decorator inputs writer.
        output_writer: Optional one-decorator output writer.
        output_reader: Optional one-decorator output reader.
        purge: Optional policy for a newly-created storage.

    Returns:
        The wrapped function, or a decorator when called with keyword options.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
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
            else SyncFolderStorage(
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
        def wrapper(
            wrapped: Callable[..., Any],
            instance: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            del instance
            cache_key: str = validate_key(_resolve_key(key_builder, args, kwargs))
            with target.lock(cache_key):
                if target.contains(cache_key):
                    return target.get(cache_key)
                output: Any = wrapped(*args, **kwargs)
                target.put(cache_key, args=args, kwargs=kwargs, output=output)
            target.prune()
            return output

        return wrapper(func)

    if fn is not None:
        return decorator(fn)
    return decorator


__all__ = ["cache"]
