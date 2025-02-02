from collections.abc import Mapping

import numpy.typing as npt
import pyvista as pv

type Attrs = Mapping[str, npt.NDArray]
type AttrsLike = pv.DataSetAttributes | Mapping[str, npt.ArrayLike]
