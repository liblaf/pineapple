import bisect
from typing import Any, TypeVar

from . import AbstractConverter, UnsupportedConversionError

_T = TypeVar("_T")


class ConversionDispatcher:
    converters: list[AbstractConverter]

    def __init__(self) -> None:
        self.converters = []

    def register(self, converter: AbstractConverter) -> None:
        bisect.insort(self.converters, converter, key=lambda c: c.priority)

    def convert(self, obj: Any, type_to: type[_T]) -> _T:
        if isinstance(obj, type_to):
            return obj
        for converter in self.converters:
            if converter.match_from(obj) and converter.match_to(type_to):
                return converter.convert(obj)
        raise UnsupportedConversionError(obj, type_to)


conversion_dispatcher = ConversionDispatcher()
register_converter = conversion_dispatcher.register
convert = conversion_dispatcher.convert
