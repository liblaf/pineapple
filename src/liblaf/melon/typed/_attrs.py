from collections.abc import Mapping

import numpy as np
import pyvista as pv
from numpy.typing import ArrayLike

type Attrs = Mapping[str, np.ndarray]
type AttrsLike = pv.DataSetAttributes | Mapping[str, ArrayLike]
