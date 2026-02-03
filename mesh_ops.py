from __future__ import annotations

from typing import Iterable, Optional, Sequence, Tuple, Union

import bpy
import bmesh
from mathutils import Vector, Matrix

from ._context import ContextError, edit_mode, preserve_selection

VecLike = Union[Vector, Tuple[float, float, float], Sequence[float]]

def _to_vec(v: VecLike) -> Vector:
    if isinstance(v, Vector):
        if len(v) != 3:
            raise ContextError(f"Expected a 3D Vector, got length {len(v)}.")
        return v.copy()
    if len(v) != 3:
        raise ContextError(f"Expected a 3-tuple/list, got length {len(v)}.")
    return Vector((float(v[0]), float(v[1]), float(v[2])))

def _require_mesh_object(obj: bpy.types.Object) -> None:
    if obj is None:
        raise ContextError("Got None. Object was not found or not returned correctly.")
    if not isinstance(obj, bpy.types.Object):
        raise ContextError(f"Expected bpy.types.Object, got {type(obj)} ({obj!r}).")
    if obj.type != "MESH":
        raise ContextError(f"Expected a MESH object, got '{obj.type}'.")
    
# region Public API

def move_mesh(obj: bpy.types.Object, direction: VecLike, distance: float = 1.0, *, space: str = "LOCAL", verts: Optional[Iterable[int]] = None) -> None:
    """
    Translate mesh geometry (vertices) by direction * distance
    
    Args:
        obj: Mesh object whose geometry (vertices) by direction * distance
        direction: 3D direction vector (e.g. (1,0,0) or Vector).
        distance: Scalar multiplier for direction.
        space: "LOCAL" or "WORLD".
        verts: Optional iterable of vertex indices to move. If None, move all verts
    
    This modifies the mesh data (like moving vertices in Edit Mode), not obj.location
    """

    _require_mesh_object(obj)

    dir_vec = _to_vec(direction)
    if dir_vec.length == 0:
        return
    
    delta = dir_vec.normalized() * float(distance)

    space = space.upper()
    if space not in ("LOCAL", "WORLD"):
        raise ContextError("Space must be 'LOCAL' or 'WORLD'")
    
    if space == "WORLD":
        inv3 = obj.matrix_world.inverted_safe().to_3x3()
        delta = inv3 @ delta

    with preserve_selection(), edit_mode(obj):
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()

        _move_bmesh(bm, delta, verts=verts)

        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
    
    return


    
# endregion

# region Pure BMesh helper

def _move_bmesh(bm: bmesh.types.BMesh, delta_local: Vector, *, verts: Optional[Iterable[int]] = None) -> None:
    """Translate vertices in the BMesh by delta_local (object local space)."""
    if verts is None:
        vlist = bm.verts
    else:
        bm.verts.ensure_lookup_table()
        vlist = [bm.verts[i] for i in verts]
    
    bmesh.ops.translate(bm, verts=list(vlist), vec=delta_local)
#endregion