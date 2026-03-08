from __future__ import annotations

from collections.abc import Iterable


class LRUMaxPolicy:
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


__all__ = ["LRUMaxPolicy"]
