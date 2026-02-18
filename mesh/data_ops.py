from __future__ import annotations
from typing import Iterable, Optional

import bpy
import numpy as np
from mathutils import Vector

from ebpy.dev.stopwatch import timer_dec

from ebpy._context import ContextError

VecLike = Iterable[float]

def move_mesh_fast(obj: bpy.types.Object, direction: VecLike, distance: float, *, space: str = "LOCAL", verts: Optional[Iterable[int]] = None):

    if obj is None or obj.type != "MESH":
        raise ContextError("Expected a mesh object.")
    
    if bpy.context.mode == "EDIT_MESH":
        raise ContextError("FAST backend can't run in Edit Mode. Use BMESH backend.")

    dist = float(distance)
    if dist == 0.0:
        return
    
    delta = Vector(direction)
    if delta.length == 0:
        return
    
    delta = delta.normalized() * distance

    sp = space.upper()
    if sp == "WORLD":
        delta = obj.matrix_world.inverted_safe().to_3x3() @ delta
    elif sp != "LOCAL":
        raise ContextError("Space must be 'LOCAL' or 'WORLD'.")
    
    me = obj.data
    n = len(me.vertices)

    co = np.empty(n * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape((n, 3))

    d = np.array(delta[:], dtype=np.float32)

    if verts is None:
        co += d
    else:
        idx = np.fromiter(verts, dtype=np.int32)
        co[idx] += d
    
    me.vertices.foreach_set("co", co.reshape(n * 3))
    me.update()