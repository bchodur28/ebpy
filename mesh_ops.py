from __future__ import annotations

from typing import Iterable, Optional, Sequence, Tuple, Union

import bpy
from mathutils import Vector
from .mesh_session import MeshSession

VecLike = Union[Vector, Tuple[float, float, float], Sequence[float]]
    
# region Public API

def move_mesh(obj: bpy.types.Object, direction: VecLike, distance: float = 1.0, *, space: str = "LOCAL", switch_to_edit: bool = True, verts: Optional[Iterable[int]] = None) -> None:
    with MeshSession(obj, switch_to_edit=switch_to_edit) as sess:
        sess.move_vertices(direction=direction, distance=distance, verts=verts, space=space)


# endregion

