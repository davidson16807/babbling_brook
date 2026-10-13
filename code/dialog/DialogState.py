# HUMAN VETTED

"""
`DialogState` is the model layer representation for a statement being formed by the player in dialog.
The statement is represented as a `Rule` tree from the languages repo 
where inflection and word order is chosen by the player
"""

from __future__ import annotations

from dataclasses import dataclass

from pyglm import glm

Address = tuple[int, ...]  # see RuleAddresses.py


@dataclass(frozen=True)
class Grid:
    """An open inflection grid: the phrase or adjective it inflects, and the inflections to choose from."""
    address: Address
    options: tuple          # `Rule` trees that read differently, in grid order


@dataclass(frozen=True)
class Press:
    """The left button went down on a chip and has not yet moved far enough to drag."""
    target: object          # a DialogLayout target
    position: glm.vec2


@dataclass(frozen=True)
class Drag:
    address: Address | None  # where the dragged node was, or None for a new one from the inventory
    node: object             # the `Rule` or word dragged
    grab: glm.vec2           # pointer offset from the dragged chip's top-left corner
    pointer: glm.vec2


@dataclass(frozen=True)
class DialogState:
    statement: object                 # the 'clause' `Rule`, in the player's order
    viewport: tuple[int, int] = (1280, 720)
    seed: int = 0                     # orders each lexeme's grid, once per dialog session
    grid: Grid | None = None
    press: Press | None = None
    drag: Drag | None = None
    inventory_scroll: int = 0         # rows
    grid_scroll: int | None = None    # rows; None scrolls to the selected inflection
    message: str = ''

# TODO: we probably need to remove the following and 

@dataclass(frozen=True)
class Spoke:
    """Outcome: the player pressed talk. `statement` is the 'clause' `Rule`, in the player's order."""
    statement: object


@dataclass(frozen=True)
class Dismissed:
    """Outcome: the player closed the dialog with nothing left open inside it."""
