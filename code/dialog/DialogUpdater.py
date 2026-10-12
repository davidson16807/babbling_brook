"""Dialog MVU transitions: press, drag, drop, click, scroll, close, and talk.

Every pointer message is resolved against `DialogLayout`, the same layout the
view draws, so a press always lands on what the player sees under the pointer.
Inflections are generated here, when a word is placed or its grid opens, and kept
in the state, so the layout never generates them. What a drop does is
`DialogDragOperations`' to say; this commits the choice it makes.
"""
import random
from dataclasses import replace

from pyglm import glm

from ..messages import (ButtonAction, FocusLostMessage, KeyboardAction, KeyboardMessage,
                        MouseButton, MouseButtonMessage, MouseMotionMessage, ScrollMessage,
                        WindowResizeMessage)
from .DialogLayout import ButtonTarget, CellTarget, ConstituentTarget, InventoryTarget
from .DialogState import Constituent, Dismissed, Drag, Grid, Press, Spoke


class DialogUpdater:
    def __init__(self, layout, *, constituents, addresses, address_operations, drag_operations,
                 lexeme, inflections, default_inflection, drag_threshold=4.0):
        """`lexeme(rule)` is the lexeme a `Rule` tree inflects, `inflections(lexeme)` generates
        every `Rule` tree of a lexeme, and `default_inflection(lexeme)` the one a newly placed
        word starts with."""
        self.layout = layout
        self.constituents = constituents
        self.addresses = addresses
        self.address_operations = address_operations
        self.drag_operations = drag_operations
        self.lexeme = lexeme
        self.inflections = inflections
        self.default_inflection = default_inflection
        self.drag_threshold = drag_threshold

    def options(self, seed, lexeme) -> tuple:
        """An inflection of `lexeme` per way it reads, in an order fixed per lexeme and dialog session.

        Seeding with a string keeps the order identical across processes; `hash()` would not.
        """
        # Inflections that read the same, word for word, such as homonyms, share a cell.
        readings = {}
        for rule in self.inflections(lexeme):
            readings.setdefault(self.constituents.words(rule), rule)
        options = list(readings.values())
        random.Random(f'{seed}/{lexeme}').shuffle(options)
        return tuple(options)

    def open(self, state, address):
        """Open the grid of the constituent at this address, scrolled to show its inflection."""
        lexeme = self.lexeme(self.addresses.resolve(state.statement, address).inflection)
        return replace(state, grid=Grid(address, self.options(state.seed, lexeme)), grid_scroll=None)

    def toggle(self, state, address):
        """Close the grid if it is the one at this address, else open that one."""
        if state.grid is not None and state.grid.address == address:
            return replace(state, grid=None)
        return self.open(state, address)

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
                return self.press(state, glm.vec2(message.position))
            return self.release(state, glm.vec2(message.position)), None
        if isinstance(message, MouseMotionMessage):
            return self.motion(state, message), None
        if isinstance(message, ScrollMessage) and message.position is not None:
            return self.scroll(state, message), None
        if isinstance(message, KeyboardMessage) and message.action == KeyboardAction.PRESS:
            if message.key == 'escape':
                return self.close(state)
            if message.key == 'e':
                return self.talk(state)
            if message.key in ('delete', 'backspace') and state.grid is not None and state.drag is None:
                statement, _, _ = self.address_operations.withdraw(state.statement, state.grid.address)
                return replace(state, statement=statement, grid=None), None
        return state, None

    def press(self, state, position):
        if state.drag is not None:
            return state, None
        target = self.layout.layout(state).hit(position)
        if isinstance(target, ButtonTarget):
            return self.talk(state) if target.name == 'talk' else self.close(state)
        if isinstance(target, CellTarget):
            statement = self.address_operations.reinflect(state.statement, state.grid.address,
                                                          state.grid.options[target.index])
            return replace(state, statement=statement, message=''), None
        if isinstance(target, (ConstituentTarget, InventoryTarget)):
            return replace(state, press=Press(target, position)), None
        return state, None

    def motion(self, state, message):
        position = glm.vec2(message.position)
        if state.drag is not None:
            return replace(state, drag=replace(state.drag, pointer=position))
        if (state.press is None or MouseButton.LEFT not in message.buttons
                or glm.distance(position, state.press.position) < self.drag_threshold):
            return state
        return replace(state, press=None, drag=self.begin(state, position), message='')

    def begin(self, state, position) -> Drag:
        target = state.press.target
        left, top, _, _ = self.layout.layout(state).anchors[target]
        grab = state.press.position - glm.vec2(left, top)
        if isinstance(target, InventoryTarget):
            new = self.constituents.arranged(self.default_inflection(target.lexeme))
            return Drag(None, new, grab, position)
        return Drag(target.address, None, grab, position)

    def release(self, state, position):
        if state.drag is not None:
            state = replace(state, drag=replace(state.drag, pointer=position))
            return self.drop(state, self.layout.layout(state).drop)
        if state.press is not None:
            return self.click(replace(state, press=None), state.press.target)
        return state

    def drop(self, state, drop):
        drag = state.drag
        state = replace(state, drag=None)
        source = drag.new if drag.address is None else drag.address
        choices = () if drop is None else self.drag_operations.choices(state.statement, source, drop)
        if len(choices) != 1:
            return state
        [choice] = choices
        grid = state.grid
        if grid is not None and choice.withdrawn is not None:
            # An open grid follows its constituent through renumbering, and closes if it was withdrawn.
            address = self.address_operations.readdress(grid.address, choice.withdrawn, choice.renamed)
            grid = None if address is None else replace(grid, address=address)
        state = replace(state, statement=choice.statement, grid=grid)
        if drag.address is None:
            # A newly placed constituent shows its grid, with its default inflection selected.
            return self.open(state, choice.address)
        return state

    def click(self, state, target):
        if isinstance(target, InventoryTarget):
            return replace(state, message='Drag a word onto the bar below to use it.')
        if isinstance(target, ConstituentTarget):
            # A child a phrase was generated with, such as its article, opens the phrase's grid.
            address = target.address
            if not isinstance(self.addresses.resolve(state.statement, address), Constituent):
                address = self.addresses.parent(address)
            return self.toggle(replace(state, message=''), address)
        return state

    def scroll(self, state, message):
        layout = self.layout.layout(state)
        panel = layout.panel(message.position)
        # Wheel up (positive y) moves toward the first row.
        step = -1 if message.offset.y > 0 else 1 if message.offset.y < 0 else 0
        if panel not in ('inventory', 'grid'):
            return state
        first = max(0, min(layout.scroll[panel] + step, layout.limits[panel]))
        return replace(state, **{f'{panel}_scroll': first})

    def close(self, state):
        """Close the innermost open thing: a drag, then the grid, then the dialog."""
        if state.drag is not None or state.press is not None:
            return replace(state, drag=None, press=None), None
        if state.grid is not None:
            # Collapsing the grid keeps whatever inflection is selected.
            return replace(state, grid=None), None
        return state, Dismissed()

    def talk(self, state):
        if state.drag is not None:
            return state, None
        if not state.statement.arrangement:
            return replace(state, message='Drag words onto the bar below, then talk.'), None
        return replace(state, grid=None, press=None), Spoke(self.constituents.ordered(state.statement))
