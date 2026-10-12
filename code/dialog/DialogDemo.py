"""Drive the dialog with synthesized pointer messages.

`dialog.py --demo` and the tests both use this, so they go through the same `DialogView.dispatch`
as a player's mouse: press, drag, scroll, and release, at points read off the layout.
"""
from pyglm import glm

from ..messages import ButtonAction, MouseButton, MouseButtonMessage, MouseMotionMessage, ScrollMessage
from .DialogLayout import CellKey, InventoryKey, PanelKey, SourceKey


class DialogDemo:
    def __init__(self, view):
        self.view = view            # see DialogView.py
        self.layout = view.layout

    def send(self, state, messages):
        for message in messages:
            state = self.view.dispatch(state, message)
        return state

    def box(self, state, predicate):
        for box in self.layout.layout(state).boxes:
            if predicate(box):
                return box
        raise LookupError('No box matches')

    def center(self, rect):
        x, y, w, h = rect
        return glm.vec2(x + w / 2, y + h / 2)

    def point(self, state, key):
        """The center of a box with `key` that no other box with a key covers."""
        layout = self.layout.layout(state)
        for box in layout.boxes:
            if box.key == key and layout.hit(self.center(box.rect)) == key:
                return self.center(box.rect)
        raise LookupError(f'{key} is not visible')

    def press(self, position):
        return MouseButtonMessage(MouseButton.LEFT, ButtonAction.PRESS, position=glm.vec2(position))

    def release(self, position):
        return MouseButtonMessage(MouseButton.LEFT, ButtonAction.RELEASE, position=glm.vec2(position))

    def move(self, position):
        return MouseMotionMessage(glm.vec2(position), glm.vec2(0), frozenset({MouseButton.LEFT}))

    def click(self, state, key):
        point = self.point(state, key)
        return self.send(state, [self.press(point), self.release(point)])

    def drag(self, state, key, destination):
        start = self.point(state, key)
        return self.send(state, [self.press(start), self.move(start + glm.vec2(8, 0)),
                                 self.move(destination), self.release(destination)])

    def playmat_end(self, state):
        """A point just right of the last placed phrase."""
        layout = self.layout.layout(state)
        bar = self.box(state, lambda box: box.key == PanelKey('playmat')).rect
        phrases = [layout.anchors[SourceKey((label,))] for label in state.statement.arrangement]
        x = phrases[-1][0] + phrases[-1][2] + 4 if phrases else bar[0] + 24
        return glm.vec2(x, bar[1] + bar[3] / 2)

    def left_of(self, state, predicate):
        x, y, w, h = self.box(state, predicate).rect
        return glm.vec2(x + 1, y + h / 2)

    def choose(self, state, text, limit=50):
        """Scroll the open grid until the cell that reads `text` shows, then click it."""
        key = CellKey(next(index for index, option in enumerate(state.grid.options)
                           if self.layout.text(option) == text))
        for wheel in (1, -1):  # up to the top, then down to the bottom
            for _ in range(limit):
                layout = self.layout.layout(state)
                if any(box.key == key for box in layout.boxes):
                    return self.click(state, key)
                grid = self.box(state, lambda box: box.key == PanelKey('grid')).rect
                state = self.send(state, [ScrollMessage(glm.vec2(0, wheel), position=self.center(grid))])
                if self.layout.layout(state).scroll['grid'] == layout.scroll['grid']:
                    break
        raise LookupError(f'{text!r} never appeared in the grid')

    def place(self, state, lexeme, text=None, destination=None):
        """Drag a lexeme from the inventory, then choose the inflection that reads `text`:
        (state, address of what was placed). Placing opens its grid, so its address is the grid's."""
        state = self.drag(state, InventoryKey(lexeme), destination or self.playmat_end(state))
        address = state.grid.address
        if text is not None:
            state = self.choose(state, text)
        return state, address

    def mockup(self, state):
        """Compose the mockup's "you give the red ball to the boy", then reopen the ball's grid."""
        state, _ = self.place(state, 'personal', 'you')
        state, _ = self.place(state, 'give')
        state, ball = self.place(state, 'ball', 'the ball')
        noun = lambda box: box.style == 'token' and box.text == 'ball'
        state, _ = self.place(state, 'red', destination=self.left_of(state, noun))
        state, _ = self.place(state, 'boy', 'to the boy')
        state = self.click(state, SourceKey(ball))
        return state
