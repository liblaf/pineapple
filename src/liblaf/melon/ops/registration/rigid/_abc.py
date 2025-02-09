from typing import Any, Protocol

from jaxtyping import Float
from numpy.typing import ArrayLike

from . import RigidRegistrationResult


class RigidRegistrationAlgorithm(Protocol):
    def register(
        self, source: Any, target: Any, *, init_transform: Float[ArrayLike, "4 4"]
    ) -> RigidRegistrationResult: ...
