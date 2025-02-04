import attrs
import numpy as np
from jaxtyping import Float


@attrs.define()
class RigidRegistrationResult:
    loss: float
    transformation: Float[np.ndarray, "4 4"]
    history: list[Float[np.ndarray, "4 4"]] = attrs.field(factory=list)
