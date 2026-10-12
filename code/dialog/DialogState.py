"""The entire dialog session model. No pygame objects or hidden widget state."""
from dataclasses import dataclass, replace
import hashlib
import random


@dataclass(frozen=True)
class DialogPiece:
    key: str
    kind: str
    text: str
    word: object = None  # DialogWord for a freely movable adjective


@dataclass(frozen=True)
class DialogWord:
    id: int
    lexeme: str
    text: str
    inflection: object  # upstream DictList, preserving every homonymous tagpoint
    pieces: tuple[DialogPiece, ...] = ()

    @property
    def surface(self):
        return ' '.join(p.word.surface if p.word else p.text for p in self.pieces) if self.pieces else self.text


@dataclass(frozen=True)
class DialogTarget:
    kind: str
    word: int | None = None
    key: str = ''


@dataclass(frozen=True)
class DialogDrag:
    source: DialogTarget
    start: tuple[float, float]
    position: tuple[float, float]
    moving: bool = False


@dataclass(frozen=True)
class DialogTurn:
    text: str
    reply: str


@dataclass(frozen=True)
class DialogState:
    session_seed: int
    words: tuple[DialogWord, ...] = ()
    next_id: int = 1
    selected: int | None = None
    grid_open: bool = False
    drag: DialogDrag | None = None
    inventory_scroll: int = 0
    grid_scroll: int = 0
    mat_scroll: int = 0
    viewport: tuple[int, int] = (1280, 800)
    turns: tuple[DialogTurn, ...] = ()
    command: object = None  # validated DialogCommand, or None on malformed input
    running: bool = True

    def find(self, id):
        for word in self.words:
            if word.id == id:
                return word
            for piece in word.pieces:
                if piece.word is not None and piece.word.id == id:
                    return piece.word
        return None

    def parent(self, id):
        return next((w for w in self.words if any(p.word and p.word.id == id for p in w.pieces)), None)

    def replace_word(self, replacement):
        return replace(self, words=tuple(
            replacement if word.id == replacement.id else replace(word, pieces=tuple(
                replace(p, word=replacement) if p.word and p.word.id == replacement.id else p
                for p in word.pieces)) for word in self.words))

    def options(self, language):
        word = self.find(self.selected)
        if word is None:
            return ()
        values = list(language.lexemes[word.lexeme].bundle)
        # Stable for the lexeme AND session, including repeated instances and reopen.
        seed = hashlib.sha256(f'{self.session_seed}:{word.lexeme}'.encode()).digest()
        random.Random(seed).shuffle(values)
        return tuple(values)


def make_word(language, lexeme, id, text=None):
    entry = language.lexemes[lexeme]
    text = entry.canonical if text is None else text
    pieces = tuple(DialogPiece(f'{kind}:{i}', kind, value)
                   for i, (kind, value) in enumerate(entry.parts[text])) if entry.kind in ('noun', 'pronoun') else ()
    return DialogWord(id, lexeme, text, language.selection(lexeme, text), pieces)


def select_form(language, word, text):
    fresh = make_word(language, word.lexeme, word.id, text)
    if not word.pieces:
        return fresh
    # Preserve the player's ordering of surviving chips and modifiers. New stock
    # chips enter in their language default positions; changing an inflection is
    # not a shortcut for correcting an existing word-order error.
    fresh_by_kind = {p.kind: p for p in fresh.pieces}
    result = [p if p.word else replace(fresh_by_kind[p.kind], key=p.key)
              for p in word.pieces if p.word or p.kind in fresh_by_kind]
    existing_kinds = {p.kind for p in result if not p.word}
    for piece in fresh.pieces:
        if piece.kind not in existing_kinds:
            rank = language.noun_order.index(piece.kind)
            index = next((i for i, p in enumerate(result) if language.noun_order.index(p.kind) > rank), len(result))
            result.insert(index, piece)
    return replace(fresh, pieces=tuple(result))
