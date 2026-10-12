"""Drag transitions of the dialog state, as xcraft's `AppDragOperations` are of its app state.

`start` begins a drag of a source; `move` follows the pointer and the drop it is over; `drop`
commits the drop, if it is allowed; `cancel` drops nothing.
"""
from dataclasses import replace

from .DragState import DragState


class DialogDragOperations:
    def __init__(self, drags, grids):
        self.drags = drags
        self.grids = grids

    def released(self, state):
        drag_type = self.drags.release()
        return replace(state, drag_type=drag_type, drag_state=drag_type.initialize())

    def start(self, state, source, point, grab):
        """Start dragging `source`, an address or a `Rule` from the inventory, from `point`, where
        `grab` is the pointer's offset from the dragged chip's top-left corner."""
        drag_type = self.drags.constituent(state.statement, source, point, grab)
        drag_state = drag_type.initialize()
        if not drag_state.candidates and not drag_state.removable:
            return state
        return replace(state, drag_type=drag_type, drag_state=drag_state, message='')

    def move(self, state, point, target):
        """Follow the pointer to `point`, over `target`, an allowed drop, or None."""
        if state.drag_type.id == DragState.released:
            return state
        return replace(state, drag_state=state.drag_type.move(state.drag_state, point, target))

    def drop(self, state, target):
        if state.drag_type.id == DragState.released:
            return state
        source = state.drag_state.source
        dropped = None if target is None else state.drag_type.drop(state.drag_state, target)
        state = self.released(state)
        if dropped is None:
            return state
        statement, address, renamed = dropped
        state = replace(state, statement=statement)
        if isinstance(source, tuple):
            return self.grids.follow(state, source, address, renamed)
        # A newly placed constituent shows its grid, with its default inflection selected.
        return self.grids.open(state, address)

    def cancel(self, state):
        return self.released(state)
