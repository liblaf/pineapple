import abc
from typing import Any


class AbstractConverter(abc.ABC):
    type_from: type
    type_to: type
    _priority: int = 0

    @abc.abstractmethod
    def convert(self, obj: Any) -> Any: ...

    @property
    def priority(self) -> int:
        return self._priority

    def match_from(self, obj: Any) -> bool:
        return isinstance(obj, self.type_from)

    def match_to(self, type_to: type) -> bool:
        return issubclass(self.type_to, type_to)
