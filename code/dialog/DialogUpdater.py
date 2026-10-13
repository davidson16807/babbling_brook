"""Dialog MVU transitions: press, drag, drop, click, scroll, close, and talk.

Every pointer message is resolved against `DialogLayout`, the same layout the
view draws, so a press always lands on what the player sees under the pointer.
Inflections are generated here, when a grid opens, and kept in the state, so the
layout never generates them.

Choosing an inflection replaces the phrase or adjective with it, exactly as the
language generated it: adjectives the player added to a phrase, and the order the
player gave its words, are wiped.
"""
import random
from dataclasses import replace

from pyglm import glm

from ..messages import (ButtonAction, FocusLostMessage, KeyboardAction, KeyboardMessage,
                        MouseButton, MouseButtonMessage, MouseMotionMessage, ScrollMessage,
                        WindowResizeMessage)
from .DialogLayout import (ButtonTarget, CellTarget, InventoryTarget, PlaceDrop, RemoveDrop,
                           WordTarget, added)
from .DialogState import Dismissed, Drag, Grid, Press, Spoke


class DialogUpdater:
    def __init__(self, layout, *, addresses, text, lexeme, inflections, default_inflection,
                 drag_threshold=4.0):
        """`text(node)` is what a `Rule` tree reads as, `lexeme(rule)` the lexeme a `Rule` tree
        inflects, `inflections(lexeme)` every `Rule` tree of a lexeme, and
        `default_inflection(lexeme)` the one a newly placed word starts with."""
        self.layout = layout
        self.addresses = addresses
        self.text = text
        self.lexeme = lexeme
        self.inflections = inflections
        self.default_inflection = default_inflection
        self.drag_threshold = drag_threshold

    def _options(self, seed, lexeme) -> tuple:
        """An inflection of `lexeme` per way it reads, in an order fixed per lexeme and dialog session.

        Seeding with a string keeps the order identical across processes; `hash()` would not.
        """
        # Inflections that read the same, such as homonyms, share a cell.
        readings = {}
        for rule in self.inflections(lexeme):
            readings.setdefault(self.text(rule), rule)
        options = list(readings.values())
        random.Random(f'{seed}/{lexeme}').shuffle(options)
        return tuple(options)

    def _inflected(self, statement, address):
        """The address of what a grid opened at this address inflects: a word that came with
        its phrase's inflection, such as its article, is inflected with its phrase."""
        parent = self.addresses.resolve(statement, address[:-1])
        return address if added(parent, self.addresses.resolve(statement, address)) else address[:-1]

    def _open(self, state, address):
        """Open the grid of what the node at this address inflects, scrolled to show its inflection."""
        address = self._inflected(state.statement, address)
        lexeme = self.lexeme(self.addresses.resolve(state.statement, address))
        return replace(state, grid=Grid(address, self._options(state.seed, lexeme)), grid_scroll=None)

    def _press(self, state, position):
        if state.drag is not None:
            return state, None
        target = self.layout.layout(state).hit(position)
        if isinstance(target, ButtonTarget):
            return self._talk(state) if target.name == 'talk' else self._close(state)
        if isinstance(target, CellTarget):
            option = state.grid.options[target.index]
            statement = self.addresses.replace(state.statement, state.grid.address, option)
            return replace(state, statement=statement, message=''), None
        if isinstance(target, (WordTarget, InventoryTarget)):
            return replace(state, press=Press(target, position)), None
        return state, None

    def _motion(self, state, message):
        position = glm.vec2(message.position)
        if state.drag is not None:
            return replace(state, drag=replace(state.drag, pointer=position))
        if (state.press is None or MouseButton.LEFT not in message.buttons
                or glm.distance(position, state.press.position) < self.drag_threshold):
            return state
        # Dragging closes the grid, so no address held in the state needs to follow the move.
        return replace(state, press=None, grid=None, drag=self._begin(state, position), message='')

    def _begin(self, state, position) -> Drag:
        target = state.press.target
        left, top, _, _ = self.layout.layout(state).anchors[target]
        grab = state.press.position - glm.vec2(left, top)
        if isinstance(target, InventoryTarget):
            return Drag(None, self.default_inflection(target.lexeme), grab, position)
        return Drag(target.address, self.addresses.resolve(state.statement, target.address), grab, position)

    def _release(self, state, position):
        if state.drag is not None:
            state = replace(state, drag=replace(state.drag, pointer=position))
            return self._drop(state, self.layout.layout(state).drop)
        if state.press is not None:
            return self._click(replace(state, press=None), state.press.target)
        return state

    def _drop(self, state, drop):
        """Move, place, or remove the dragged node. A drop is addressed in the statement
        without the dragged node, as the layout showed it."""
        drag = state.drag
        state = replace(state, drag=None)
        if drop is None:
            return state
        statement = state.statement
        if drag.address is not None:
            statement = self.addresses.remove(statement, drag.address)
        if isinstance(drop, RemoveDrop):
            return replace(state, statement=statement)
        statement = self.addresses.insert(statement, drop.parent, drop.index, drag.node)
        state = replace(state, statement=statement)
        if drag.address is None:
            # A newly placed word shows its grid, with its default inflection selected.
            return self._open(state, (*drop.parent, drop.index))
        return state

    def _click(self, state, target):
        if isinstance(target, InventoryTarget):
            return replace(state, message='Drag a word onto the bar below to use it.')
        if isinstance(target, WordTarget):
            state = replace(state, message='')
            if state.grid is not None and state.grid.address == self._inflected(state.statement, target.address):
                return replace(state, grid=None)
            return self._open(state, target.address)
        return state

    def _scroll(self, state, message):
        layout = self.layout.layout(state)
        panel = layout.panel(message.position)
        # Wheel up (positive y) moves toward the first row.
        step = -1 if message.offset.y > 0 else 1 if message.offset.y < 0 else 0
        if panel not in ('inventory', 'grid'):
            return state
        first = max(0, min(layout.scroll[panel] + step, layout.limits[panel]))
        return replace(state, **{f'{panel}_scroll': first})

    def _close(self, state):
        """Close the innermost open thing: a drag, then the grid, then the dialog."""
        if state.drag is not None or state.press is not None:
            return replace(state, drag=None, press=None), None
        if state.grid is not None:
            # Collapsing the grid keeps whatever inflection is selected.
            return replace(state, grid=None), None
        return state, Dismissed()

    def _talk(self, state):
        if state.drag is not None:
            return state, None
        if not state.statement.content:
            return replace(state, message='Drag words onto the bar below, then talk.'), None
        return replace(state, grid=None, press=None), Spoke(state.statement)

    def update(self, state, message):
        """Return (state, outcome), where outcome is None, `Spoke`, or `Dismissed`."""
        if isinstance(message, WindowResizeMessage):
            return replace(state, viewport=message.size), None
        if isinstance(message, FocusLostMessage):
            # The release may never arrive, so drop whatever was held.
            return replace(state, press=None, drag=None), None
        if (isinstance(message, MouseButtonMessage) and message.button == MouseButton.LEFT
                and message.position is not None):
            if message.action == ButtonAction.PRESS:
                return self._press(state, glm.vec2(message.position))
            return self._release(state, glm.vec2(message.position)), None
        if isinstance(message, MouseMotionMessage):
            return self._motion(state, message), None
        if isinstance(message, ScrollMessage) and message.position is not None:
            return self._scroll(state, message), None
        if isinstance(message, KeyboardMessage) and message.action == KeyboardAction.PRESS:
            if message.key == 'escape':
                return self._close(state)
            if message.key == 'e':
                return self._talk(state)
            if message.key in ('delete', 'backspace') and state.grid is not None and state.drag is None:
                # A grid is only ever open on something the player added, so it can be removed.
                statement = self.addresses.remove(state.statement, state.grid.address)
                return replace(state, statement=statement, grid=None), None
        return state, None
