from typing import Any, Protocol

from . import RigidRegistrationResult


class RigidRegistrationAlgorithm(Protocol):
    def register(self, source: Any, target: Any) -> RigidRegistrationResult: ...
