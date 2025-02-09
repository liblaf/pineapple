from typing import Any

import numpy as np
from jaxtyping import Float
from numpy.typing import ArrayLike

from . import RigidICP, RigidRegistrationAlgorithm, RigidRegistrationResult


def rigid_align(
    source: Any,
    target: Any,
    *,
    algorithm: RigidRegistrationAlgorithm | None = None,
    init_transform: Float[ArrayLike, "4 4"] | None = None,
) -> RigidRegistrationResult:
    algorithm = algorithm or RigidICP()
    init_transform = np.eye(4) if init_transform is None else init_transform
    result: RigidRegistrationResult = algorithm.register(
        source, target, init_transform=init_transform
    )
    return result
