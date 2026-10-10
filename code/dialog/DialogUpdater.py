"""Dialog MVU transitions: press, drag, drop, click, scroll, close, and talk.

Every pointer message is resolved against `DialogLayout`, the same layout the
view draws, so a press always lands on what the player sees under the pointer.
"""
from dataclasses import replace

from pyglm import glm

from ..messages import (ButtonAction, FocusLostMessage, KeyboardAction, KeyboardMessage,
                        MouseButton, MouseButtonMessage, MouseMotionMessage, ScrollMessage,
                        WindowResizeMessage)
from .DialogLayout import (ButtonTarget, CellTarget, InventoryTarget, PhraseDrop,
                           PlaymatDrop, RemoveDrop, WordTarget)
from .DialogState import Dismissed, Drag, Press, Spoke, Word
from .playmat import find, insert_modifier, reinflect, without


class DialogUpdater:
    def __init__(self, layout, drag_threshold=4.0):
        self.layout = layout
        self.lexicon = layout.lexicon
        self.drag_threshold = drag_threshold

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
                return self.remove(state, state.grid), None
        return state, None

    def press(self, state, position):
        if state.drag is not None:
            return state, None
        target = self.layout.layout(state).hit(position)
        if isinstance(target, ButtonTarget):
            return self.talk(state) if target.name == 'talk' else self.close(state)
        if isinstance(target, CellTarget):
            playmat = reinflect(state.playmat, target.id, target.inflection)
            return replace(state, playmat=playmat, message=''), None
        if isinstance(target, (WordTarget, InventoryTarget)):
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
            lexeme = self.lexicon.lexemes[target.lexeme]
            return Drag(Word(state.next_id, lexeme.id, lexeme.default), False, grab, position)
        return Drag(find(state.playmat, target.id), True, grab, position)

    def release(self, state, position):
        if state.drag is not None:
            state = replace(state, drag=replace(state.drag, pointer=position))
            return self.drop(state, self.layout.layout(state).drop)
        if state.press is not None:
            return self.click(replace(state, press=None), state.press.target)
        return state

    def drop(self, state, drop):
        word, fresh = state.drag.word, not state.drag.from_playmat
        state = replace(state, drag=None)
        if drop is None:
            return state
        playmat = without(state.playmat, word.id)
        if isinstance(drop, RemoveDrop):
            return self.remove(state, word.id)
        if isinstance(drop, PlaymatDrop):
            playmat = (*playmat[:drop.index], word, *playmat[drop.index:])
        elif isinstance(drop, PhraseDrop):
            phrase = find(playmat, drop.id)
            inflection = self.lexicon.lexemes[phrase.lexeme].inflection(phrase.inflection)
            phrase = insert_modifier(phrase, inflection, word, drop.index)
            playmat = tuple(phrase if item.id == phrase.id else item for item in playmat)
        if fresh:
            # A newly placed word shows its grid, with its default inflection selected.
            return replace(state, playmat=playmat, next_id=state.next_id + 1,
                           grid=word.id, grid_scroll=None)
        return replace(state, playmat=playmat)

    def click(self, state, target):
        if isinstance(target, InventoryTarget):
            return replace(state, message='Drag a word onto the bar below to use it.')
        if isinstance(target, WordTarget):
            return replace(state, grid=None if state.grid == target.id else target.id,
                           grid_scroll=None, message='')
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
        playmat = without(state.playmat, id)
        grid = state.grid if state.grid is not None and find(playmat, state.grid) is not None else None
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
        return replace(state, grid=None, press=None), Spoke(state.playmat)
