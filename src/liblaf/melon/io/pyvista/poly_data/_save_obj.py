import collections
import functools
from pathlib import Path

import numpy as np
import pyvista as pv
from jaxtyping import Integer

from liblaf.melon.typed import StrPath


def save_obj(path: StrPath, mesh: pv.PolyData) -> None:
    if not has_groups(mesh):
        mesh.save(path)
    with Path(path).open("w") as fp:
        fprint = functools.partial(print, file=fp)
        for v in mesh.points:
            fprint("v", *v)
        if "GroupIds" in mesh.cell_data:
            group_ids: Integer[np.ndarray, " N"] = mesh.cell_data["GroupIds"]
            if "GroupNames" in mesh.field_data:
                group_names = mesh.field_data["GroupNames"]
            else:
                group_names = collections.defaultdict(str)
            last_group_id: int = -1
            for f, group_id in zip(mesh.irregular_faces, group_ids, strict=True):
                if group_id != last_group_id:
                    group_name: str = group_names[group_id]  # pyright: ignore[reportAssignmentType]
                    if group_name:
                        fprint("g", group_name)
                    else:
                        fprint("g")
                    last_group_id = group_id
                fprint("f", *[v + 1 for v in f])
        else:
            for f in mesh.irregular_faces:
                fprint("f", *[v + 1 for v in f])


def has_groups(mesh: pv.PolyData) -> bool:
    if "GroupIds" not in mesh.cell_data:
        return False
    group_ids: Integer[np.ndarray, " N"] = mesh.cell_data["GroupIds"]
    return len(np.unique(group_ids)) != 1
