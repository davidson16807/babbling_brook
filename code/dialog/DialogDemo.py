"""Drive the real updater with synthesized pointer messages.

`dialog.py --demo` and the tests both use this, so they go through the same
press, drag, scroll, and release path as a player's mouse.
"""
from pyglm import glm

from ..messages import (ButtonAction, MouseButton, MouseButtonMessage,
                        MouseMotionMessage, ScrollMessage)
from .DialogLayout import CellTarget, InventoryTarget, PanelTarget, WordTarget


class DialogDemo:
    def __init__(self, updater):
        self.updater = updater
        self.layout = updater.layout

    def send(self, state, messages):
        outcomes = []
        for message in messages:
            state, outcome = self.updater.update(state, message)
            if outcome is not None:
                outcomes.append(outcome)
        return state, outcomes

    def box(self, state, predicate):
        for box in self.layout.layout(state).boxes:
            if predicate(box):
                return box
        raise LookupError('No box matches')

    def center(self, rect):
        x, y, w, h = rect
        return glm.vec2(x + w / 2, y + h / 2)

    def point(self, state, target):
        """The center of a box for `target` that isn't covered by another target."""
        layout = self.layout.layout(state)
        for box in layout.boxes:
            if box.target == target and layout.hit(self.center(box.rect)) == target:
                return self.center(box.rect)
        raise LookupError(f'{target} is not visible')

    def press(self, position):
        return MouseButtonMessage(MouseButton.LEFT, ButtonAction.PRESS, position=glm.vec2(position))

    def release(self, position):
        return MouseButtonMessage(MouseButton.LEFT, ButtonAction.RELEASE, position=glm.vec2(position))

    def move(self, position):
        return MouseMotionMessage(glm.vec2(position), glm.vec2(0), frozenset({MouseButton.LEFT}))

    def click(self, state, target):
        point = self.point(state, target)
        return self.send(state, [self.press(point), self.release(point)])

    def drag(self, state, target, destination):
        start = self.point(state, target)
        return self.send(state, [self.press(start), self.move(start + glm.vec2(8, 0)),
                                 self.move(destination), self.release(destination)])

    def playmat_end(self, state):
        """A point just right of the last placed word."""
        layout = self.layout.layout(state)
        bar = self.box(state, lambda box: box.target == PanelTarget('playmat')).rect
        words = [layout.anchors[WordTarget(word.id)] for word in state.playmat]
        x = words[-1][0] + words[-1][2] + 4 if words else bar[0] + 24
        return glm.vec2(x, bar[1] + bar[3] / 2)

    def left_of(self, state, predicate):
        x, y, w, h = self.box(state, predicate).rect
        return glm.vec2(x + 1, y + h / 2)

    def choose(self, state, id, inflection, limit=50):
        """Scroll the open grid until `inflection` shows, then click it."""
        target = CellTarget(id, inflection)
        for wheel in (1, -1):  # up to the top, then down to the bottom
            for _ in range(limit):
                layout = self.layout.layout(state)
                if any(box.target == target for box in layout.boxes):
                    return self.click(state, target)
                grid = self.box(state, lambda box: box.target == PanelTarget('grid')).rect
                state, _ = self.send(state, [ScrollMessage(glm.vec2(0, wheel), position=self.center(grid))])
                if self.layout.layout(state).scroll['grid'] == layout.scroll['grid']:
                    break
        raise LookupError(f'{inflection!r} never appeared in the grid')

    def place(self, state, lexeme, inflection=None, destination=None):
        """Drag a lexeme from the inventory and pick an inflection: (state, word id)."""
        id = state.next_id
        state, _ = self.drag(state, InventoryTarget(lexeme), destination or self.playmat_end(state))
        if inflection is not None:
            state, _ = self.choose(state, id, inflection)
        return state, id

    def mockup(self, state):
        """Compose the mockup's "you give the red ball to the boy", then reopen the ball's grid."""
        state, _ = self.place(state, 'pronoun', 'you')
        state, _ = self.place(state, 'give')
        state, ball = self.place(state, 'ball', 'the ball')
        noun = lambda box: box.style == 'token' and box.text == 'ball'
        state, _ = self.place(state, 'red', destination=self.left_of(state, noun))
        state, _ = self.place(state, 'boy', 'to the boy')
        state, _ = self.click(state, WordTarget(ball))
        return state
