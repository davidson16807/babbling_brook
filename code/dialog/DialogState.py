"""Model for composing a statement. Everything the dialog GUI remembers is here.

Positions, sizes, and grid cells are never stored: `DialogLayout` derives them
from this state whenever they are needed, for drawing and for hit-testing alike.
"""
from __future__ import annotations

from dataclasses import dataclass

from pyglm import glm


@dataclass(frozen=True)
class Slot:
    """A word that comes with a noun phrase's inflection, such as its article or adposition.

    It is the `index`th token of `part` in whichever inflection the phrase has.
    """
    part: str
    index: int = 0


@dataclass(frozen=True)
class Word:
    """A lexeme placed on the playmat, as one chip or one noun phrase."""
    id: int                                  # stable for the dialog session
    lexeme: str
    inflection: str                          # text of the chosen inflection
    # Noun phrases only: their words in the player's order, as the slots of the
    # inflection's tokens and the adjectives placed among them.
    arrangement: tuple[Slot | Word, ...] = ()


@dataclass(frozen=True)
class Press:
    """The left button went down on a chip and has not yet moved far enough to drag."""
    target: object  # a DialogLayout target
    position: glm.vec2


@dataclass(frozen=True)
class Drag:
    item: Word | Slot     # a new Word when it comes from the inventory
    phrase: int | None    # id of the noun phrase the item is dragged out of, if any
    from_playmat: bool
    grab: glm.vec2        # pointer offset from the dragged chip's top-left corner
    pointer: glm.vec2


@dataclass(frozen=True)
class DialogState:
    viewport: tuple[int, int] = (1280, 720)
    seed: int = 0                     # orders every inflection grid, once per dialog session
    playmat: tuple[Word, ...] = ()
    grid: int | None = None           # id of the word whose inflection grid is open
    press: Press | None = None
    drag: Drag | None = None
    inventory_scroll: int = 0         # rows
    grid_scroll: int | None = None    # rows; None scrolls to the selected inflection
    next_id: int = 1
    message: str = ''


@dataclass(frozen=True)
class Spoke:
    """Outcome: the player pressed talk. `playmat` is the statement as arranged."""
    playmat: tuple[Word, ...]


@dataclass(frozen=True)
class Dismissed:
    """Outcome: the player closed the dialog with nothing left open inside it."""
