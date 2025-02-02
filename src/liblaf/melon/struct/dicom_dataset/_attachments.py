from collections.abc import Iterable, Iterator, Mapping, MutableMapping
from pathlib import Path
from typing import Any

from liblaf import melon
from liblaf.melon.typing import StrPath


class Attachments(MutableMapping[str, Any]):
    root: Path
    _data: dict[str, Any]
    _keys: set[str]

    def __init__(
        self,
        root: StrPath | None = None,
        data: Mapping[str, Any] | None = None,
        keys: Iterable[str] | None = None,
    ) -> None:
        self.root = Path(root or ".")
        self._data = dict(data) if data else {}
        self._keys = set(keys) if keys else set()

    def __getitem__(self, key: str) -> Any:
        if key not in self._data:
            self._data[key] = melon.load(self.root / key)
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._keys.add(key)

    def __delitem__(self, key: str) -> None:
        del self._data[key]
        self._keys.remove(key)

    def __iter__(self) -> Iterator[str]:
        yield from self._keys

    def __len__(self) -> int:
        return len(self._keys)

    def save(self, path: StrPath) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        for key, value in self.items():
            melon.save(path / key, value)
