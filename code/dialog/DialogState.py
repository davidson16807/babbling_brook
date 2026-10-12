"""Model for composing a statement. Everything the dialog GUI remembers is here.

Positions and sizes are never stored: `DialogLayout` derives them from this state
whenever they are needed, for drawing and for hit-testing alike. Inflections are
the languages repo's `Rule` trees (see dialog/Constituents.py), generated when a word
is placed or its grid opens, and kept here; drawing never generates them.
"""
from __future__ import annotations

from dataclasses import dataclass

from pyglm import glm


Label = tuple[str, int]  # a constituent's child: the `index`th child of its part, e.g. ('det', 0)


@dataclass(frozen=True)
class Constituent:
    """A `Rule` as the language generated it, the constituents the player added to it,
    and the arrangement of all its children; see dialog/Constituents.py.

    The statement is a constituent, with an empty 'clause' `Rule` and only added
    children: the phrases the player placed. So are those phrases, and the adjectives
    added to a noun phrase. A constituent is reached by its address, the labels from
    the statement down to it; the statement's address is ().
    """
    inflection: object                      # `Rule` tree of the chosen inflection
    added: tuple[Constituent, ...] = ()     # in the order the player added them
    arrangement: tuple[Label, ...] = ()     # every child's label, in the player's order


@dataclass(frozen=True)
class Grid:
    """An open inflection grid: the constituent it inflects, and every inflection of its lexeme."""
    address: tuple[Label, ...]
    options: tuple          # `Rule` trees that read differently, in grid order


@dataclass(frozen=True)
class Press:
    """The left button went down on a chip and has not yet moved far enough to drag."""
    target: object  # a DialogLayout target
    position: glm.vec2


@dataclass(frozen=True)
class Drag:
    address: tuple[Label, ...] | None   # of the child dragged, or None for a new one from the inventory
    new: Constituent | None             # the new one from the inventory
    grab: glm.vec2        # pointer offset from the dragged chip's top-left corner
    pointer: glm.vec2


@dataclass(frozen=True)
class DialogState:
    statement: Constituent            # what the player has composed, from an empty 'clause' `Rule`
    viewport: tuple[int, int] = (1280, 720)
    seed: int = 0                     # orders each lexeme's grid, once per dialog session
    grid: Grid | None = None
    press: Press | None = None
    drag: Drag | None = None
    inventory_scroll: int = 0         # rows
    grid_scroll: int | None = None    # rows; None scrolls to the selected inflection
    message: str = ''


@dataclass(frozen=True)
class Spoke:
    """Outcome: the player pressed talk. `statement` is the 'clause' `Rule`, its children as arranged."""
    statement: object


@dataclass(frozen=True)
class Dismissed:
    """Outcome: the player closed the dialog with nothing left open inside it."""
