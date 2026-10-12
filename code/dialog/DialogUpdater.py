"""Dialog MVU transitions: press, drag, drop, click, scroll, close, and talk.

Every pointer message is resolved against `DialogLayout`, the same layout the
view draws, so a press always lands on what the player sees under the pointer.
Inflections are generated here, when a word is placed or its grid opens, and kept
in the state, so the layout never generates them.
"""
import random
from dataclasses import replace

from pyglm import glm

from ..messages import (ButtonAction, FocusLostMessage, KeyboardAction, KeyboardMessage,
                        MouseButton, MouseButtonMessage, MouseMotionMessage, ScrollMessage,
                        WindowResizeMessage)
from .DialogLayout import (ButtonTarget, CellTarget, ChildTarget, InventoryTarget, PhraseDrop,
                           PlaymatDrop, RemoveDrop, WordTarget)
from .DialogState import Dismissed, Drag, Grid, Press, Spoke


class DialogUpdater:
    def __init__(self, layout, inflections, default_inflection, drag_threshold=4.0):
        """`inflections(lexeme)` generates every `Rule` tree of a lexeme, and
        `default_inflection(lexeme)` the one a newly placed word starts with."""
        self.layout = layout
        self.playmats = layout.playmats
        self.noun_phrases = layout.playmats.noun_phrases
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
            readings.setdefault(self.noun_phrases.words(rule), rule)
        options = list(readings.values())
        random.Random(f'{seed}/{lexeme}').shuffle(options)
        return tuple(options)

    def open(self, state, id, label=None):
        """Open the grid of the word with this id, or of its added child with this label,
        scrolled to show its inflection."""
        word = self.playmats.find(state.playmat, id)
        lexeme = word.lexeme if label is None else self.noun_phrases.addition(word, label)[0]
        return replace(state, grid=Grid(id, label, self.options(state.seed, lexeme)), grid_scroll=None)

    def toggle(self, state, id, label=None):
        """Close the grid if it is the one for this word or child, else open that one."""
        if state.grid is not None and (state.grid.id, state.grid.label) == (id, label):
            return replace(state, grid=None)
        return self.open(state, id, label)

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
                if state.grid.label is None:
                    return self.remove(state, state.grid.id), None
                phrase, _ = self.noun_phrases.withdrawn(self.playmats.find(state.playmat, state.grid.id),
                                                        state.grid.label)
                return replace(state, playmat=self.playmats.replaced(state.playmat, phrase), grid=None), None
        return state, None

    def press(self, state, position):
        if state.drag is not None:
            return state, None
        target = self.layout.layout(state).hit(position)
        if isinstance(target, ButtonTarget):
            return self.talk(state) if target.name == 'talk' else self.close(state)
        if isinstance(target, CellTarget):
            grid, inflection = state.grid, state.grid.options[target.index]
            word = self.playmats.find(state.playmat, grid.id)
            word = (self.playmats.reinflected(word, inflection) if grid.label is None
                    else self.noun_phrases.reinflected_child(word, grid.label, inflection))
            return replace(state, playmat=self.playmats.replaced(state.playmat, word), message=''), None
        if isinstance(target, (WordTarget, ChildTarget, InventoryTarget)):
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
            word = self.playmats.placed(target.lexeme, self.default_inflection(target.lexeme), state.next_id)
            return Drag(word, None, False, grab, position)
        if isinstance(target, ChildTarget):
            return Drag(target.label, target.id, True, grab, position)
        return Drag(self.playmats.find(state.playmat, target.id), None, True, grab, position)

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
        if drop is None:
            return state
        if drag.phrase is not None:
            return self.drop_child(state, drag, drop)
        word = drag.item
        if isinstance(drop, RemoveDrop):
            return self.remove(state, word.id)
        if isinstance(drop, PhraseDrop):
            # An adjective from the inventory becomes a child of the phrase, with its grid open.
            phrase, label = self.noun_phrases.adopted(self.playmats.find(state.playmat, drop.id),
                                                      word.lexeme, word.inflection, drop.index)
            return self.open(replace(state, playmat=self.playmats.replaced(state.playmat, phrase)), phrase.id, label)
        state = replace(state, playmat=self.playmats.inserted(state.playmat, word, drop.index))
        if not drag.from_playmat:
            # A newly placed word shows its grid, with its default inflection selected.
            return self.open(replace(state, next_id=state.next_id + 1), word.id)
        return state

    def drop_child(self, state, drag, drop):
        """Drop a child dragged out of a noun phrase: move it within the phrase, into another, or away."""
        source = self.playmats.find(state.playmat, drag.phrase)
        if isinstance(drop, PhraseDrop) and drop.id == source.id:
            phrase = self.noun_phrases.moved(source, drag.item, drop.index)
            return replace(state, playmat=self.playmats.replaced(state.playmat, phrase))
        # Withdrawing an added child renumbers the others, so a grid open on one closes.
        source, (lexeme, inflection) = self.noun_phrases.withdrawn(source, drag.item)
        playmat = self.playmats.replaced(state.playmat, source)
        grid = None if state.grid is not None and state.grid.id == source.id and state.grid.label else state.grid
        if isinstance(drop, PhraseDrop):
            phrase, _ = self.noun_phrases.adopted(self.playmats.find(playmat, drop.id), lexeme, inflection, drop.index)
            playmat = self.playmats.replaced(playmat, phrase)
        return replace(state, playmat=playmat, grid=grid)

    def click(self, state, target):
        if isinstance(target, InventoryTarget):
            return replace(state, message='Drag a word onto the bar below to use it.')
        if isinstance(target, WordTarget):
            return self.toggle(replace(state, message=''), target.id)
        if isinstance(target, ChildTarget):
            # An added child has a grid of its own; a child the phrase came with opens the phrase's.
            phrase = self.playmats.find(state.playmat, target.id)
            label = target.label if self.noun_phrases.is_added(phrase, target.label) else None
            return self.toggle(replace(state, message=''), target.id, label)
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

    def remove(self, state, id):
        playmat = self.playmats.without(state.playmat, id)
        grid = state.grid if state.grid is not None and self.playmats.find(playmat, state.grid.id) is not None else None
        return replace(state, playmat=playmat, grid=grid)

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
        if not state.playmat:
            return replace(state, message='Drag words onto the bar below, then talk.'), None
        return replace(state, grid=None, press=None), Spoke(self.playmats.statement(state.playmat))
