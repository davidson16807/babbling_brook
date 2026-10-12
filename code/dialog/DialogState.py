"""Model for composing a statement. Everything the dialog GUI remembers is here.

Positions and sizes are never stored: `DialogLayout` derives them from this state
whenever they are needed, for drawing and for hit-testing alike. Inflections are
the languages repo's `Rule` trees (see dialog/NounPhrases.py), generated when a word
is placed or its grid opens, and kept here; drawing never generates them.
"""
from __future__ import annotations

from dataclasses import dataclass

from pyglm import glm


Label = tuple[str, int]  # a noun phrase's child: the `index`th child of its part, e.g. ('det', 0)


@dataclass(frozen=True)
class Word:
    """A lexeme placed on the playmat, as one chip or one noun phrase.

    A noun phrase's children are those of its inflection that read as something
    (adposition, article, noun, ...) followed by those the player added (adjectives,
    and determiners such as "this"). Labels address them: each part of speech is
    counted over the generated children first, then the added ones. Labels are
    internal to the dialog; see dialog/NounPhrases.py.
    """
    id: int                                  # stable for the dialog session
    lexeme: str
    inflection: object                       # `Rule` tree of the chosen inflection
    added: tuple[tuple[str, object], ...] = ()   # noun phrases: (lexeme, `Rule`) of each added child
    arrangement: tuple[Label, ...] = ()          # noun phrases: every child's label, in the player's order


@dataclass(frozen=True)
class Grid:
    """An open inflection grid: what it inflects, and every inflection of that lexeme."""
    id: int                 # the word on the playmat
    label: Label | None     # the added child of that noun phrase it inflects, or None for the word itself
    options: tuple          # `Rule` trees that read differently, in grid order


@dataclass(frozen=True)
class Press:
    """The left button went down on a chip and has not yet moved far enough to drag."""
    target: object  # a DialogLayout target
    position: glm.vec2


@dataclass(frozen=True)
class Drag:
    item: Word | Label    # a word (new when it comes from the inventory), or a noun phrase's child
    phrase: int | None    # id of the noun phrase a child is dragged out of
    from_playmat: bool
    grab: glm.vec2        # pointer offset from the dragged chip's top-left corner
    pointer: glm.vec2


@dataclass(frozen=True)
class DialogState:
    viewport: tuple[int, int] = (1280, 720)
    seed: int = 0                     # orders each lexeme's grid, once per dialog session
    playmat: tuple[Word, ...] = ()
    grid: Grid | None = None
    press: Press | None = None
    drag: Drag | None = None
    inventory_scroll: int = 0         # rows
    grid_scroll: int | None = None    # rows; None scrolls to the selected inflection
    next_id: int = 1
    message: str = ''


@dataclass(frozen=True)
class Spoke:
    """Outcome: the player pressed talk. `statement` is a `Rule` tree per word, as arranged."""
    statement: tuple


@dataclass(frozen=True)
class Dismissed:
    """Outcome: the player closed the dialog with nothing left open inside it."""
