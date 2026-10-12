"""`DialogState` contains all dialog state. Model values are immutable.

Inflections are the languages repo's `Rule` trees. Where the player puts them is kept as
arrangements, and what the player refers to is kept as addresses; see
ConstituentAddresses.py. Positions and sizes are never stored: `DialogLayout` derives
them whenever they are needed, for drawing and for hit-testing alike.
"""
from __future__ import annotations

from dataclasses import dataclass

Label = tuple[str, int]                 # a child: the `index`th child of its part of speech, e.g. ('det', 0)
Arrangement = tuple[Label, ...]         # children, in the player's order
Address = tuple[Label, ...]             # labels from the statement down to a child; () is the statement


@dataclass(frozen=True)
class Constituent:
    """A `Rule` as the language generated it, the constituents the player added to it, and
    its arrangement: the label of every child, in the player's order.

    The statement is a constituent, with an empty 'clause' `Rule` whose children are all
    added: the phrases the player placed. So are those phrases, and the adjectives added to
    a noun phrase.
    """
    inflection: object                      # `Rule`
    added: tuple[Constituent, ...] = ()     # in the order the player added them
    arrangement: Arrangement = ()


@dataclass(frozen=True)
class Grid:
    """An open inflection grid: the constituent it inflects, and every inflection of its lexeme."""
    address: Address
    options: tuple          # `Rule`s that read differently, in grid order


@dataclass(frozen=True)
class Spoke:
    """Outcome: the player pressed talk. `statement` is the 'clause' `Rule`, its children as arranged."""
    statement: object


@dataclass(frozen=True)
class Dismissed:
    """Outcome: the player closed the dialog with nothing left open inside it."""


@dataclass(frozen=True)
class DialogState:
    statement: Constituent
    drag_type: object                   # see ConstituentDrags.py
    drag_state: object                  # the drag type's value
    grid: Grid | None = None
    viewport: tuple[int, int] = (1280, 720)
    seed: int = 0                       # orders each lexeme's grid, once per dialog session
    inventory_scroll: int = 0           # rows
    grid_scroll: int | None = None      # rows; None scrolls to the selected inflection
    message: str = ''
    outcome: Spoke | Dismissed | None = None   # for whatever opened the dialog to act on
