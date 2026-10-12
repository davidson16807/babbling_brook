"""`DialogUpdater` is the update function in the Model-View-Updater architecture, as xcraft's
`AppUpdater` is. Each transition takes the prior state and what the player did, in the dialog's
own terms (addresses, points, drops, cells), and returns a new `DialogState`. It never sees
input devices: `DialogView.dispatch` turns messages into these calls.
"""
from dataclasses import replace

from .DialogState import Dismissed, Spoke
from .DragState import DragState


class DialogUpdater:
    def __init__(self, drag_operations, grids, addresses, address_operations, default_inflection):
        """`default_inflection(lexeme)` generates the `Rule` a newly placed word of a lexeme starts with."""
        self.drag_operations = drag_operations    # see DialogDragOperations.py
        self.grids = grids                        # see DialogGrids.py
        self.addresses = addresses
        self.address_operations = address_operations
        self.default_inflection = default_inflection

    def drag_start(self, state, address, point, grab):
        """Start dragging the placed constituent or child at this address."""
        return self.drag_operations.start(state, address, point, grab)

    def drag_start_lexeme(self, state, lexeme, point, grab):
        """Start dragging a new word of this lexeme from the inventory, in its default inflection."""
        return self.drag_operations.start(state, self.default_inflection(lexeme), point, grab)

    def drag_move(self, state, point, target):
        return self.drag_operations.move(state, point, target)

    def drag_drop(self, state, target):
        return self.drag_operations.drop(state, target)

    def drag_cancel(self, state):
        return self.drag_operations.cancel(state)

    def grid_toggle(self, state, address):
        return self.grids.toggle(replace(state, message=''), address)

    def grid_choose(self, state, index):
        return self.grids.choose(replace(state, message=''), index)

    def hint(self, state, message):
        return replace(state, message=message)

    def remove(self, state):
        """Remove the constituent whose grid is open."""
        if state.grid is None or state.drag_type.id != DragState.released:
            return state
        statement, _, _ = self.address_operations.withdraw(state.statement, state.grid.address)
        return replace(state, statement=statement, grid=None)

    def scroll(self, state, panel, first):
        """Show the panel ('inventory' or 'grid') from row `first`."""
        return replace(state, **{f'{panel}_scroll': first})

    def resize(self, state, viewport):
        return replace(state, viewport=viewport)

    def close(self, state):
        """Close the innermost open thing: a drag, then the grid, then the dialog."""
        if state.drag_type.id != DragState.released:
            return self.drag_cancel(state)
        if state.grid is not None:
            return self.grids.close(state)
        return replace(state, outcome=Dismissed())

    def talk(self, state):
        if state.drag_type.id != DragState.released:
            return state
        if not state.statement.arrangement:
            return replace(state, message='Drag words onto the bar below, then talk.')
        return replace(state, grid=None, outcome=Spoke(self.addresses.rule(state.statement)))
