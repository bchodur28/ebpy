from __future__ import annotations
import bpy

from ebpy._context import ContextError, _require_view_layer  # internal dependency

# region Public API region 

def select_object_by_name(name: str, *, make_active: bool = True, deselect_others: bool = True) -> bpy.types.Object:
    """
    Select an object by name in the active view layer

    Returns:
        The selected by bpy.types.Object.

    Raises:
        ContextError: If the object does not exists or is not selectable
    """

    v1 = _require_view_layer()

    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ContextError(f"Object '{name}' is not in the active view layer")
    
    if deselect_others:
        for o in list(bpy.context.selected_objects):
            try:
                o.select_set(False)
            except Exception:
                pass

    try:
        obj.select_set(True)
    except Exception as e:
        raise ContextError(f"Could not select object '{name}': {e}")
    
    if make_active:
        try:
            v1.objects.active = obj
        except Exception as e:
            raise ContextError(f"Could not set '{name}' as active: {e}")
        
    return obj

    

# endregion