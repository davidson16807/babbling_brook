"""Immutable model values for dialog composition.

The language library calls a tag-axis mapping a ``dictstore``.  ``DictStore``
is the small, immutable value used at the GUI boundary.  Adapters can construct
it from the language repository's mutable dictstores without leaking those
objects (or their tags) into the view.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping, TypeAlias


PartOfSpeech: TypeAlias = Literal['pronoun', 'noun', 'verb', 'adjective']


@dataclass(frozen=True, slots=True)
class DictStore:
    """Hashable tagpoint preserving one possible reading of an inflection."""

    entries: tuple[tuple[str, str], ...]

    @classmethod
    def of(cls, values: Mapping[str, object] | None = None, **kwargs) -> 'DictStore':
        merged = {**(values or {}), **kwargs}
        return cls(tuple(sorted((key, str(value)) for key, value in merged.items())))

    def get(self, key: str, default=None):
        return dict(self.entries).get(key, default)

    def as_dict(self) -> dict[str, str]:
        return dict(self.entries)


@dataclass(frozen=True, slots=True)
class Inflection:
    """One visible string and every tagpoint that can produce that string."""

    text: str
    tagpoints: tuple[DictStore, ...]


@dataclass(frozen=True, slots=True)
class Lexeme:
    id: str
    term: str
    part_of_speech: PartOfSpeech
    canonical: str
    inflections: tuple[Inflection, ...]


@dataclass(frozen=True, slots=True)
class PhraseToken:
    role: Literal['adposition', 'determiner', 'adjective', 'noun']
    text: str
    lexeme_id: str | None
    tagpoints: tuple[DictStore, ...]


@dataclass(frozen=True, slots=True)
class WordItem:
    id: int
    lexeme_id: str
    text: str
    tagpoints: tuple[DictStore, ...]


@dataclass(frozen=True, slots=True)
class NounPhraseItem:
    id: int
    noun_lexeme_id: str
    tokens: tuple[PhraseToken, ...]


PlaymatItem: TypeAlias = WordItem | NounPhraseItem


@dataclass(frozen=True, slots=True)
class DragState:
    kind: Literal['inventory', 'item', 'adjective']
    source_id: str | int
    position: tuple[int, int]
    origin: tuple[int, int]
    phrase_id: int | None = None
    moved: bool = False


@dataclass(frozen=True, slots=True)
class DialogState:
    lexemes: tuple[Lexeme, ...]
    playmat: tuple[PlaymatItem, ...] = ()
    viewport: tuple[int, int] = (1280, 720)
    session_seed: int = 16807
    next_id: int = 1
    active_item_id: int | None = None
    drag: DragState | None = None
    feedback: str = 'Build a sentence, then talk.'
    running: bool = True

    def lexeme(self, lexeme_id: str) -> Lexeme:
        return next(item for item in self.lexemes if item.id == lexeme_id)

    def item(self, item_id: int) -> PlaymatItem | None:
        return next((item for item in self.playmat if item.id == item_id), None)
