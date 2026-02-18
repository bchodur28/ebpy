from __future__ import annotations
from typing import Iterable, Optional, Sequence, Tuple, Union
from mathutils import Vector

import bpy

from ebpy._context import ContextError
from .backend import MeshBackend
from .bmesh_session import BMeshSession
from .data_ops import move_mesh_fast


VecLike = Union[Vector, Tuple[float, float, float], Sequence[float]]
    
# region Public API

def move_mesh(obj: bpy.types.Object, direction: VecLike, distance: float = 1.0, *, space: str = "LOCAL", backend: MeshBackend = MeshBackend.AUTO, verts: Optional[Iterable[int]] = None) -> None:
    
    if backend == MeshBackend.FAST:
        # FAST is only safe outside Edit Mode
        if bpy.context.mode == "EDIT_MESH":
            raise ContextError("FAST backend can't run in Edit Mode. Use AUTO or BMESH")
        return move_mesh_fast(obj, direction, distance, space=space, verts=verts)

    if backend == MeshBackend.AUTO:
        # SAFE AUTO: only use FAST when we're not in edit mesh
        if bpy.context.mode != "EDIT_MESH":
            return move_mesh_fast(obj, direction, distance, space=space, verts=verts)

    with BMeshSession(obj, switch_to_edit=True) as sess:
        sess.move_vertices(direction=direction, distance=distance, verts=verts, space=space)


# endregion

