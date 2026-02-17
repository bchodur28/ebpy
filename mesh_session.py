from __future__ import annotations
from contextlib import contextmanager
from typing import Iterable, List, Optional

import bpy
import bmesh
from mathutils import Vector

from ebpy.stopwatch import timer_dec

from ._context import ContextError, edit_mode, object_mode, preserve_selection

VecLike = Iterable[float]

class MeshSession:
    """
    Context maager that opens a BMESH for the given object, 
    yields a session object with convenient methods, and writes back on exit.
    """

    def __init__(self, obj: bpy.types.Object, *, switch_to_edit: bool = True):
        if obj is None or not isinstance(obj, bpy.types.Object):
            raise ContextError("Expected a bpy.types.Object")
        if obj.type != "MESH":
            raise ContextError(f"Expected MESH object, got '{obj.type}'.")
        self.obj = obj
        self.switch_to_edit = bool(switch_to_edit)

        # These are set when context is entered
        self._bm: Optional[bmesh.types.BMesh] = None
        self._in_edit_mode: Optional[bool] = None
        self._is_temp_bm = False

    def __enter__(self) -> "MeshSession":
        if self.switch_to_edit:
            # edit_mode context ensures the active object + mode switching and selection preserved
            self._mode_cm = edit_mode(self.obj)
            self._mode_cm.__enter__()
            self._in_edit_mode = True
            self._bm = bmesh.from_edit_mesh(self.obj.data)
            self._is_temp_bm = False
        else:
            # Use a temporary BMesh (object-mode workflow)
            self._mode_cm = None
            self._in_edit_mode = False
            self._bm = bmesh.new()
            self._bm.from_mesh(self.obj.data)
            self._is_temp_bm = True

        # Helpful to ensure lookups and normals are up-to-date
        self._bm.verts.ensure_lookup_table()
        self._bm.faces.ensure_lookup_table()
        self._bm.normal_update()
        return self
    
    def __exit__(self, exc_type, exc, tb):
        try:
            if self._bm is None:
                return False
            
            # If a temporary BMesh, wirte back via to_mesh
            if self._is_temp_bm:
                self._bm.to_mesh(self.obj.data)
                self.obj.data.update()
            else:
                # edit-mode bmesh: update edit mesh
                bmesh.update_edit_mesh(self.obj.data, loop_triangles=False, destructive=False)
        finally:
            # free only if we created it
            if self._is_temp_bm and self._bm is not None:
                self._bm.free()
            self._bm = None

            if self.switch_to_edit:
                # exit edit_mode context manager
                self._mode_cm.__exit__(exc_type, exc, tb)

    def get_vertex_indices(self, *, selected_only: bool = True) -> List[int]:
        """Return list of vertex indices (ints) in this mesh (in current BM)"""
        if self._bm is None:
            raise ContextError("Mesh is not entered")
        self._bm.verts.ensure_lookup_table()
        if selected_only:
            return [v.index for v in self._bm.verts if v.select]
        else:
            return [v.index for v in self._bm.verts]

    @timer_dec  
    def move_vertices(self, direction: VecLike, distance: float, *, space: str = "LOCAL", verts: Optional[Iterable[int]] = None):
        """Translate given vertices (indices) by direction * distance."""
        bm = self._bm
        if bm is None:
            raise ContextError("MeshSession is not entered.")
        
        dist = float(distance)
        if dist == 0.0:
            return
        
        delta = Vector(direction)
        if delta.length == 0:
            return
        
        delta = delta.normalized() * distance

        sp = space.upper()
        if sp == "WORLD":
            delta = self.obj.matrix_world.inverted_safe().to_3x3() @ delta
        elif sp != "LOCAL":
            raise ContextError("Space must be 'LOCAL' or 'WORLD'.")
        
        verts_seq = bm.verts
        d = delta

        if verts is None:
            for v in bm.verts:
                v.co += d
                
        else:
            verts_seq.ensure_lookup_table()
            for i in verts:
                verts_seq[i].co += d

        
