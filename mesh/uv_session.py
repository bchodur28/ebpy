from __future__ import annotations
from typing import Iterable, List, Optional, Sequence, Tuple, Union
from mathutils import Vector

import bpy
import bmesh

from ebpy._context import ContextError, edit_mode
from .bmesh_session import BMeshSession

Vec2Like = Union[Vector, Tuple[float, float], Sequence[float]]

class UVSession:
    """
    Context manager for working with UVs on a mesh object.

    This wraps a BMeshSession and provides UV-specific helpers for:
    - accessing the active UV layer
    - getting selected UV loops
    - translating UVs
    - scaling UVs
    """

    def __int__(self, obj: bpy.types.Object, *, switch_to_edit: bool = True):
        if obj is None or not isinstance(obj, bpy.types.Object):
            raise ContextError("Expected a bpy.types.Object")
        if obj.type != "MESH":
            raise ContextError(f"Expected MESH object, got '{obj.type}'.")
        
        self.obj = obj
        self.switch_to_edit = switch_to_edit
        self._mesh_session: Optional[BMeshSession] = None

    def __enter__(self) -> "UVSession":
        self._mesh_session = BMeshSession(self.obj, switch_to_edit=self.switch_to_edit)
        self._mesh_session.__enter__()

        bm = self.get_bm()
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            uv_layer = bm.loops.layers.uv.new()

        return self
    
    def __exit__(self, exc_type, exc, tb):
        if self._mesh_session is not None:
            return self._mesh_session.__exit__(exc_type, exc, tb)
        return False

    def get_bm(self) -> bmesh.types.BMesh:
        if self._mesh_session is None:
            raise ContextError("UV session is not entered.")
        return self._mesh_session.get_bm()
    
    def get_uv_layer(self) -> bmesh.types.BMLayerItem:
        bm = self.get_bm()
        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            uv_layer = bm.loops.layers.uv.new()
        return uv_layer
    
