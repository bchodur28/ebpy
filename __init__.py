"""
ebpy — Easy Blender Python

A higher-level helper library built on top of Blender's bpy API,
with a focus on BMesh-first, context-safe mesh operations.
"""

# Public errors
from .stopwatch import timer_dec
from ._context import ContextError
from .mesh_ops import move_mesh
from .select import select_object_by_name
from .mesh_session import MeshSession

__all__ = [
    "timer_dec",
    "ContextError",
    "move_mesh",
    "select_object_by_name",
    "MeshSession",
    "move_vertices"
]
