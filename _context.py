from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Optional, Sequence, Tuple

import bpy

# region Errors
class ContextError(RuntimeError):
    """Base error for context helper failure"""

class ModeError(ContextError):
    pass

class AreaOverrideError(RuntimeError):
    pass

# endregion

# region Small Helpers

def _is_object_mode() -> bool:
    return bpy.context.mode == "OBJECT"

def _is_edit_mode() -> bool:
    # Edit_MESH, EDIT_CURVE are different EDIT modes
    return bpy.context.mode.startswith("EDIT")

def _require_object(obj: bpy.types.Object) -> None:
    if obj is None:
        raise ContextError("Object is None.")
    if not isinstance(obj, bpy.types.Object):
        raise ContextError(f"Expected bpy.types.Object, got {type(obj)}.")
    
def _require_view_layer() -> bpy.types.ViewLayer:
    v1 = bpy.context.view_layer
    if v1 is None:
        raise ContextError("No active view layer in context.")
    return v1
    
#endregion

#region State snapshots

@dataclass(frozen=True)
class SelectionState:
    """Snapshot of selction + active object for later restore."""
    active_name: Optional[str]
    selected_names: Tuple[str, ...]

def capture_selection() -> SelectionState:
    v1 = _require_view_layer()
    active = v1.objects.active
    selected = tuple(o.name for o in bpy.context.selected_objects)
    return SelectionState(
        active_name=(active.name if active else None), 
        selected_names=selected
    )

def restore_selection(state: SelectionState, *, deselect_all_first: bool = True) -> None:
    v1 = _require_view_layer()

    if deselect_all_first:
        for o in bpy.context.selected_objects:
            o.select_set(False)

    # Restore selected
    for name in state.selected_names:
        obj = bpy.data.objects.get(name)
        if obj:
            obj.select_set(True)

    # Restore active
    if state.active_name:
        active = bpy.data.objects.get(state.active_name)
        if active:
            v1.objects.active = active

# endregion

# region Context managers

@contextmanager
def preserve_selection(*, restore: bool = True) -> Iterator[None]:
    state = capture_selection()
    try:
        yield
    finally:
        if restore:
            restore_selection(state)

@contextmanager
def set_active(obj: bpy.types.Object, *, select: bool = True) -> Iterator[None]:
    _require_object(obj)
    with preserve_selection():
        if select:
            obj.select_set(True)
        _require_view_layer().objects.active = obj
        yield

@contextmanager
def mode(obj: bpy.types.Objects, target_mode: str) -> Iterator[None]:
    """
    Ensure Blender is in target_mode for obj, 
    then restore previous mode + selection. target_mode: "OBJECT" or "EDIT
    """
    _require_object(obj)
    target_mode = target_mode.upper()

    prev_mode = bpy.context.mode

    with set_active(obj):
        try:
            if target_mode == "OBJECT":
                if not _is_object_mode():
                    bpy.ops.object.mode_set(mode="OBJECT")
            elif target_mode == "EDIT":
                if not _is_edit_mode():
                    bpy.ops.object.mode_set(mode="EDIT")
            else:
                raise ModeError(f"Unsupported target_mode '{target_mode}'. Use 'OBJECT' or 'EDIT'.")
            
            yield
        finally:
            try:
                if prev_mode == "OBJECT":
                    if not _is_object_mode():
                        bpy.ops.object.mode_set(mode="OBJECT")
                    elif prev_mode.startswith("EDIT"):
                        if not _is_edit_mode():
                            bpy.ops.object.mode_set(mode="EDIT")
            except Exception:
                pass

@contextmanager    
def edit_mode(obj: bpy.types.Object) -> Iterator[None]:
    with mode(obj, "EDIT"):
        yield

@contextmanager    
def object_mode(obj: bpy.types.Object) -> Iterator[None]:
    with mode(obj, "OBJECT"):
        yield

# endregion

# region UI overrides

def _find_area(area_type: str) -> Optional[bpy.types.Area]:
    win = bpy.context.window
    if not win or not win.screen:
        return None
    for area in win.screen.areas:
        if area.type == area_type:
            return area
    return None

def _find_region(area: bpy.types.Area, region_type: str) -> Optional[bpy.types.Region]:
    for region in area.regions:
        if region.type == region_type:
            return region
    return None

def override_area(area_type: str, *, region_type: str = "WINDOW") -> Iterator[dict]:
    """For ops that require a UI Area (often uv-related)."""
    area = _find_area(area_type)
    if area is None:
        raise AreaOverrideError(f"Could not find area of type '{area_type}' in current screen.")
    
    region = _find_region(area, region_type)
    if region is None:
        raise AreaOverrideError(f"Could not find region '{region} in area '{area_type}'")
    
    override = {
        "window": bpy.context.window,
        "screen": bpy.context.window.screen,
        "area": area,
        "region": region
    }

    yield override

# endregion