from __future__ import annotations

from typing import Any

from liblaf.pineapple._src.shared.types import KeyBuilder


def _resolve_key(
    key_builder: KeyBuilder, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> str:
    value: Any = key_builder(*args, **kwargs)
    if not isinstance(value, str):
        raise TypeError
    return value


__all__ = ["_resolve_key"]
