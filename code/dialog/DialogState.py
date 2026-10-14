# HUMAN VETTED

"""
`DialogState` is the model layer representation for a statement being formed by the player in dialog.
The statement is represented as a `DialogRule` tree (see inflection/DialogRule.py)
where inflection and word order is chosen by the player
"""

from __future__ import annotations

from dataclasses import dataclass

from pyglm import glm

Address = tuple[int, ...]  # see RuleAddresses.py


@dataclass(frozen=True)
class GridState:
    """An open inflection grid: the phrase or adjective it inflects, and the inflections to choose from."""
    address: Address
    options: tuple          # `DialogRule` trees that read differently, in grid order


@dataclass(frozen=True)
class PressState:
    """The left button went down on a chip and has not yet moved far enough to drag."""
    target: object          # a DialogLayout target
    position: glm.vec2


@dataclass(frozen=True)
class DragState:
    address: Address | None  # where the dragged node was, or None for a new one from the inventory
    node: object             # the `DialogRule` or word dragged
    grab: glm.vec2           # pointer offset from the dragged chip's top-left corner
    pointer: glm.vec2


@dataclass(frozen=True)
class DialogState:
    statement: object                 # the 'clause' `DialogRule`, in the player's order
    viewport: tuple[int, int] = (1280, 720)
    seed: int = 0                     # orders each lexeme's grid, once per dialog session
    grid: GridState | None = None
    press: PressState | None = None
    drag: DragState | None = None
    inventory_scroll: int = 0         # rows
    grid_scroll: int | None = None    # rows; None scrolls to the selected inflection
    message: str = ''
    is_spoken: bool = False           # true only in the state returned by the update that spoke `statement`
