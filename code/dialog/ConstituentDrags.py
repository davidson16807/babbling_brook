"""Drag types, as xcraft's `RelationDrags` makes them: each has an `id` from `DragState`, and
`initialize()`, `move(value, point, target)`, and `drop(value, target)` over its immutable
value. The state keeps the drag type in progress as `drag_type`, and its value as `drag_state`.

`constituent` is a drag of a placed constituent, a child a phrase was generated with, or a
`Rule` from the inventory; `release` is no drag at all.
"""
from dataclasses import dataclass, replace

from pyglm import glm

from .DragState import DragState


@dataclass(frozen=True)
class DragValue:
    source: object          # an address, or a `Rule` dragged from the inventory
    start: glm.vec2         # pointer, where the drag started
    current: glm.vec2       # pointer, now
    grab: glm.vec2          # pointer offset from the dragged chip's top-left corner
    candidates: tuple       # addresses of the constituents the source may be placed in
    removable: bool         # whether dropping the source on the inventory removes it
    target: object = None   # the drop under the pointer, if it is allowed: a `PlaceDrop` or `RemoveDrop`


@dataclass(frozen=True)
class ConstituentDrag:
    drag_operations: object     # see ConstituentDragOperations.py
    statement: object           # as it was when the drag started
    source: object
    start: glm.vec2
    grab: glm.vec2
    id = DragState.constituent

    def initialize(self):
        return DragValue(self.source, self.start, self.start, self.grab,
                         self.drag_operations.targets(self.statement, self.source),
                         self.drag_operations.removable(self.statement, self.source))

    def move(self, value, point, target):
        return replace(value, current=point, target=target)

    def drop(self, value, target):
        return self.drag_operations.drop(self.statement, value.source, target)


@dataclass(frozen=True)
class ReleasedDrag:
    id = DragState.released

    def initialize(self):
        return None

    def move(self, value, point, target):
        return value

    def drop(self, value, target):
        return None


class ConstituentDrags:
    def __init__(self, drag_operations):
        self.drag_operations = drag_operations

    def constituent(self, statement, source, start, grab):
        return ConstituentDrag(self.drag_operations, statement, source, glm.vec2(start), glm.vec2(grab))

    def release(self):
        return ReleasedDrag()
