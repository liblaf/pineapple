from typing import Any

import numpy as np
from jaxtyping import Float
from numpy.typing import ArrayLike

from liblaf import melon

from . import RigidICP, RigidRegistrationAlgorithm, RigidRegistrationResult


def rigid_align(
    source: Any,
    target: Any,
    *,
    algorithm: RigidRegistrationAlgorithm | None = None,
    init_transform: Float[ArrayLike, "4 4"] | None = None,
) -> RigidRegistrationResult:
    algorithm = algorithm or RigidICP()
    init_transform: Float[np.ndarray, "4 4"] = (
        np.eye(4) if init_transform is None else np.asarray(init_transform)
    )
    source = melon.transform(source, init_transform)
    result: RigidRegistrationResult = algorithm.register(source, target)
    result.transformation = melon.concat_transforms(
        result.transformation, init_transform
    )
    for i in range(len(result.history)):
        result.history[i] = melon.concat_transforms(result.history[i], init_transform)
    return result
