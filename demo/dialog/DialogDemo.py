"""Drive the real updater with synthesized pointer messages.

`main.py --demo` uses this to compose a statement through the same press, drag,
scroll, and release path as a player's mouse. Like `main.py`, it is not part of the
babbling_brook package.
"""
from pyglm import glm

from babbling_brook.messages import (ButtonAction, MouseButton, MouseButtonMessage,
                        MouseMotionMessage, ScrollMessage)
from babbling_brook.dialog.DialogLayout import CellTarget, InventoryTarget, PanelTarget, WordTarget


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
        """Drag `target` to `destination`: a point, or a function of the state once the drag
        has begun, when the dragged word has left its place and the rest have closed up."""
        start = self.point(state, target)
        state, outcomes = self.send(state, [self.press(start), self.move(start + glm.vec2(8, 0))])
        if callable(destination):
            destination = destination(state)
        state, more = self.send(state, [self.move(destination), self.release(destination)])
        return state, outcomes + more

    def playmat_end(self, state):
        """A point just right of the last placed word."""
        layout = self.layout.layout(state)
        bar = self.box(state, lambda box: box.target == PanelTarget('playmat')).rect
        words = [layout.anchors[WordTarget((index,))] for index in range(len(state.statement.content))]
        x = words[-1][0] + words[-1][2] + 4 if words else bar[0] + 24
        return glm.vec2(x, bar[1] + bar[3] / 2)

    def left_of(self, state, predicate):
        x, y, w, h = self.box(state, predicate).rect
        return glm.vec2(x + 1, y + h / 2)

    def choose(self, state, inflection, limit=50):
        """Scroll the open grid until the inflection that reads as `inflection` shows, then click it."""
        text = self.updater.text
        target = CellTarget(next(index for index, option in enumerate(state.grid.options)
                                 if text(option) == inflection))
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
        """Drag a lexeme from the inventory and pick an inflection: (state, address of what was placed).

        Placing opens the new word's grid, so its address is the grid's.
        """
        state, _ = self.drag(state, InventoryTarget(lexeme), destination or self.playmat_end(state))
        address = state.grid.address
        if inflection is not None:
            state, _ = self.choose(state, inflection)
        return state, address

    def mockup(self, state):
        """Compose the mockup's "you give the red ball to the boy", then reopen the ball's grid.

        The ball is inflected before "red" is added, since choosing an inflection wipes adjectives.
        """
        state, _ = self.place(state, 'personal', 'you')
        state, _ = self.place(state, 'give')
        state, ball = self.place(state, 'ball', 'the ball')
        noun = lambda box: box.style == 'token' and box.text == 'ball'
        state, _ = self.place(state, 'red', destination=self.left_of(state, noun))
        state, _ = self.place(state, 'boy', 'to the boy')
        state, _ = self.click(state, WordTarget(ball))
        return state
