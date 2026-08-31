from __future__ import annotations

import decimal
import re
from collections.abc import Iterable

_SIZE_PATTERN = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>B|K(?:I?B)?|M(?:I?B)?|G(?:I?B)?|T(?:I?B)?)?",
    re.IGNORECASE,
)
_SIZE_FACTORS = {
    "": 1,
    "B": 1,
    "K": 1024,
    "KB": 1024,
    "KIB": 1024,
    "M": 1024**2,
    "MB": 1024**2,
    "MIB": 1024**2,
    "G": 1024**3,
    "GB": 1024**3,
    "GIB": 1024**3,
    "T": 1024**4,
    "TB": 1024**4,
    "TIB": 1024**4,
}


class LRUMaxPolicy:
    """Select least-recently-used entries until resource limits are met.

    Args:
        max_bytes: Maximum aggregate entry size, or `None` to ignore size.
        max_entries: Maximum number of entries, or `None` to ignore count.

    Raises:
        ValueError: If both limits are `None`.
    """

    def __init__(
        self, *, max_bytes: int | None = None, max_entries: int | None = None
    ) -> None:
        if max_bytes is None and max_entries is None:
            raise ValueError
        self._max_bytes = max_bytes
        self._max_entries = max_entries

    def select_keys(
        self,
        *,
        total_bytes: int,
        total_entries: int,
        lru_entries: Iterable[tuple[str, int]],
    ) -> list[str]:
        remaining_bytes = total_bytes
        remaining_entries = total_entries
        keys_to_delete: list[str] = []

        def exceeds_limits() -> bool:
            too_many_bytes = (
                self._max_bytes is not None and remaining_bytes > self._max_bytes
            )
            too_many_entries = (
                self._max_entries is not None and remaining_entries > self._max_entries
            )
            return too_many_bytes or too_many_entries

        for key, size_bytes in lru_entries:
            if not exceeds_limits():
                break
            keys_to_delete.append(key)
            remaining_bytes -= size_bytes
            remaining_entries -= 1

        return keys_to_delete


class Purge(LRUMaxPolicy):
    """LRU purge policy with a binary human-readable size limit.

    Args:
        size: Non-negative byte count or binary size such as `"4G"` or
            `"1.5 KiB"`. `None` disables the size limit.
        max_entries: Optional maximum number of ready entries.

    Examples:
        >>> Purge(size="1 KiB").select_keys(
        ...     total_bytes=1025,
        ...     total_entries=2,
        ...     lru_entries=[("old", 1), ("new", 1024)],
        ... )
        ['old']
    """

    def __init__(
        self,
        size: int | str | None = "4G",
        *,
        max_entries: int | None = None,
    ) -> None:
        super().__init__(
            max_bytes=None if size is None else _parse_size(size),
            max_entries=max_entries,
        )


def _parse_size(size: int | str) -> int:
    if isinstance(size, bool):
        message = "size must be an integer byte count or a size string"
        raise TypeError(message)
    if isinstance(size, int):
        if size < 0:
            message = "size must be non-negative"
            raise ValueError(message)
        return size
    match = _SIZE_PATTERN.fullmatch(size.strip())
    if match is None:
        message = f"invalid cache size: {size!r}"
        raise ValueError(message)
    value = decimal.Decimal(match.group("value"))
    factor = _SIZE_FACTORS[(match.group("unit") or "").upper()]
    bytes_ = value * factor
    if bytes_ != bytes_.to_integral_value():
        message = f"cache size does not resolve to whole bytes: {size!r}"
        raise ValueError(message)
    return int(bytes_)


__all__ = ["LRUMaxPolicy", "Purge"]
