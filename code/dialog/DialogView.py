"""`DialogView` draws the dialog and wires input to `DialogUpdater`, as xcraft's `AppView` does.

`draw(state)` lays the state out and hands its boxes, styled, to a UI adapter. `dispatch(state,
message)` plays the part of `AppView.wire`'s event listeners: for a pointer message, it finds what
lies under the pointer in the same layout the player sees, as `elementFromPoint` does, and calls the
updater with that key. A press on a word starts a drag at once, as `pointerdown` does; a release
that has not moved past the drag threshold is a click instead.
"""
from pyglm import glm

from ..messages import (ButtonAction, FocusLostMessage, KeyboardAction, KeyboardMessage, MouseButton,
                        MouseButtonMessage, MouseMotionMessage, ScrollMessage, WindowResizeMessage)
from ..view.UiBox import UiBox, UiBoxStyle
from .DialogLayout import ButtonKey, CellKey, InventoryKey, SourceKey
from .DragState import DragState

PANEL = (22, 33, 37, 230)       # the explorer and editor panel colors
LINE = (147, 169, 146, 255)
DIM_LINE = (98, 120, 104, 255)
CREAM = (239, 241, 223)
AMBER = (243, 222, 166)
CHIP = (48, 66, 70, 255)
NONE = (0, 0, 0, 0)


def dialog_styles(font_size=22):
    def style(background, border, border_width=1, text_color=CREAM):
        return UiBoxStyle(background, border, border_width, text_color, font_size)
    selected = style(CHIP, (*AMBER, 255), 3, AMBER)
    return {
        'panel': style(PANEL, LINE),
        'chip': style(CHIP, LINE),
        'chip-selected': selected,
        'chip-dragged': style((64, 86, 90, 235), (*AMBER, 255), 2),
        'token': style(NONE, DIM_LINE),
        'phrase': style((30, 44, 48, 255), LINE),
        'phrase-selected': style((30, 44, 48, 255), (*AMBER, 255), 3),
        'phrase-dragged': style((40, 58, 62, 235), (*AMBER, 255), 2),
        'cell': style(CHIP, DIM_LINE),
        'cell-selected': selected,
        'track': style((14, 22, 25, 255), NONE, 0),
        'thumb': style(LINE, NONE, 0),
        'caret': style((*AMBER, 255), NONE, 0),
        'remove': style((120, 46, 40, 200), (200, 90, 80, 255), 2),
        'close': style((150, 58, 52, 255), (200, 90, 80, 255)),
        'talk': style((66, 120, 74, 255), (140, 190, 140, 255)),
        'message': style(NONE, NONE, 0, AMBER),
    }


class DialogView:
    def __init__(self, layout, updater, ui, styles):
        self.layout = layout        # see DialogLayout.py
        self.updater = updater      # see DialogUpdater.py
        self.ui = ui                # with `draw(viewport, boxes)` and `release()`, e.g. `PygameUiBoxView`
        self.styles = styles

    def boxes(self, state) -> tuple[UiBox, ...]:
        return tuple(UiBox(box.rect, self.styles[box.style], box.text) for box in self.layout.layout(state).boxes)

    def draw(self, state):
        self.ui.draw(state.viewport, self.boxes(state))

    def dispatch(self, state, message):
        """The state after the player's `message`."""
        updater = self.updater
        if isinstance(message, WindowResizeMessage):
            return updater.resize(state, message.size)
        if isinstance(message, FocusLostMessage):
            # The release may never arrive, so drop whatever was held.
            return updater.drag_cancel(state)
        if isinstance(message, KeyboardMessage) and message.action == KeyboardAction.PRESS:
            if message.key == 'escape':
                return updater.close(state)
            if message.key == 'e':
                return updater.talk(state)
            if message.key in ('delete', 'backspace'):
                return updater.remove(state)
            return state
        if isinstance(message, ScrollMessage) and message.position is not None:
            layout = self.layout.layout(state)
            panel = layout.panel(glm.vec2(message.position))
            if panel not in ('inventory', 'grid'):
                return state
            # Wheel up (positive y) moves toward the first row.
            step = -1 if message.offset.y > 0 else 1 if message.offset.y < 0 else 0
            return updater.scroll(state, panel, max(0, min(layout.scroll[panel] + step, layout.limits[panel])))
        dragging = state.drag_type.id != DragState.released
        if isinstance(message, MouseMotionMessage) and dragging:
            point = glm.vec2(message.position)
            moved = updater.drag_move(state, point, None)
            return updater.drag_move(state, point, self.layout.layout(moved).drop(point))
        if (isinstance(message, MouseButtonMessage) and message.button == MouseButton.LEFT
                and message.position is not None):
            point = glm.vec2(message.position)
            if message.action == ButtonAction.PRESS:
                return self.pointer_down(state, point)
            if dragging:
                return self.pointer_up(state, point)
        return state

    def pointer_down(self, state, point):
        if state.drag_type.id != DragState.released:
            return state
        layout = self.layout.layout(state)
        key = layout.hit(point)
        if isinstance(key, ButtonKey):
            return self.updater.talk(state) if key.name == 'talk' else self.updater.close(state)
        if isinstance(key, CellKey):
            return self.updater.grid_choose(state, key.index)
        if isinstance(key, (SourceKey, InventoryKey)):
            left, top, _, _ = layout.anchors[key]
            grab = point - glm.vec2(left, top)
            if isinstance(key, SourceKey):
                return self.updater.drag_start(state, key.address, point, grab)
            started = self.updater.drag_start_lexeme(state, key.lexeme, point, grab)
            return started if started is not state else self.updater.hint(state, 'There is nowhere to put that yet.')
        return state

    def pointer_up(self, state, point):
        source = state.drag_state.source
        if glm.distance(point, state.drag_state.start) >= self.layout.metrics.drag_threshold:
            moved = self.updater.drag_move(state, point, None)
            return self.updater.drag_drop(state, self.layout.layout(moved).drop(point))
        # A click: what was pressed was not dragged.
        state = self.updater.drag_cancel(state)
        if isinstance(source, tuple):
            return self.updater.grid_toggle(state, source)
        return self.updater.hint(state, 'Drag a word onto the bar below to use it.')

    def release(self):
        self.ui.release()
