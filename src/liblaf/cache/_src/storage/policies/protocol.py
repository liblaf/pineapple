from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol


class PrunePolicy(Protocol):
    def select_keys(
        self,
        *,
        total_bytes: int,
        total_entries: int,
        lru_entries: Iterable[tuple[str, int]],
    ) -> list[str]: ...


__all__ = ["PrunePolicy"]
