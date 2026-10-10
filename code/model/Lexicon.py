"""A language's playable vocabulary: what the dialog shows, and what it can mean.

`inflection/` generates lexicons at startup with the languages repo
(github.com/davidson16807/languages); these classes don't depend on it.
Tagpoints are the complete dictkeys that were rendered, defaults included.
The text of an inflection may have several interpretations. English "give" is
any present plural or a 1st/2nd person singular, for instance. Every
interpretation is kept as a tagpoint in the inflection's `tagpoints`, so that
a statement checker can later choose the one that agrees with the rest of the
sentence. The player only ever sees `Token.text`.
"""
from dataclasses import dataclass
from typing import TypeAlias

# A hashable dictstore: sorted (tagaxis, tag) pairs, e.g. (('number', 'plural'), ...).
Tagpoint: TypeAlias = tuple[tuple[str, str], ...]

NOUN_PHRASE_PARTS = frozenset({'noun', 'pronoun'})


def tagpoint(tags: dict[str, str]) -> Tagpoint:
    return tuple(sorted(tags.items()))


@dataclass(frozen=True)
class Token:
    part: str  # 'adposition', 'det', 'adj', 'n', 'v', or 'vp' (as for the auxiliary "will")
    text: str


@dataclass(frozen=True)
class Inflection:
    tokens: tuple[Token, ...]
    tagpoints: tuple[Tagpoint, ...]

    @property
    def text(self) -> str:
        return ' '.join(token.text for token in self.tokens)


@dataclass(frozen=True)
class Lexeme:
    id: str
    part: str      # 'noun', 'pronoun', 'verb', or 'adjective'
    display: str   # inventory text, in the foreign language
    default: str   # text of the inflection that is selected when the word is placed
    inflections: tuple[Inflection, ...]  # unique by text, in generation order

    @property
    def is_noun_phrase(self) -> bool:
        return self.part in NOUN_PHRASE_PARTS

    def inflection(self, text: str) -> Inflection:
        for inflection in self.inflections:
            if inflection.text == text:
                return inflection
        raise KeyError(f'{self.id!r} has no inflection {text!r}')


@dataclass(frozen=True)
class Lexicon:
    language: str
    # Treat as a value: replace, don't mutate.
    lexemes: dict[str, Lexeme]

    def sorted(self) -> tuple[Lexeme, ...]:
        """Inventory order: pronouns, then alphabetical by displayed text."""
        return tuple(sorted(self.lexemes.values(),
                            key=lambda lexeme: (lexeme.part != 'pronoun', lexeme.display.casefold())))
