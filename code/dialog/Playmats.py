"""Arrows on the playmat: the statement the player composes, and the words placed on it.

A playmat is a tuple of `Word`s. A word is a lexeme with one of its inflections, as
a `Rule` tree; a noun phrase also has an arrangement, whose adjectives are words too.
What leaves the dialog is `statement`, a `Rule` tree per word in the player's order.
"""
from dataclasses import replace

from .DialogState import Slot, Word


class Playmats:
    """
    `Playmats` is a category whose objects are playmats and the words on them, and
    whose arrows place, find, move, reinflect, and remove words, and read a playmat
    as the words or the `Rule` trees of its statement. It is built from
    `Arrangements`, for the order within each noun phrase and the reading of `Rule`s.
    """
    def __init__(self, arrangements):
        self.arrangements = arrangements

    def placed(self, lexeme: str, inflection, id: int) -> Word:
        """A newly placed word of `lexeme`, with the `Rule` tree `inflection`."""
        word = Word(id, lexeme, inflection)
        return replace(word, arrangement=self.arrangements.slots(inflection)) if inflection.tag == 'np' else word

    def reinflected(self, word, inflection) -> Word:
        """`word` with the `Rule` tree `inflection`; a phrase keeps the player's order where it can."""
        word = replace(word, inflection=inflection)
        return replace(word, arrangement=self.arrangements.arrange(word.arrangement, inflection)) \
            if word.inflection.tag == 'np' else word

    def items(self, word) -> list[tuple[object, str]]:
        """(slot or adjective, text) for each item of a noun phrase, in the player's order."""
        return self.arrangements.items(word.arrangement, word.inflection)

    def slot_text(self, word, slot: Slot) -> str:
        return self.arrangements.texts(word.inflection)[slot]

    def text(self, word) -> str:
        """What `word` reads as, with a phrase's words in the player's order."""
        return ' '.join(self.tokens((word,)))

    def index(self, options, inflection) -> int:
        """The index of the option among `options` that reads as `inflection`, word for word."""
        return [self.arrangements.words(option) for option in options].index(self.arrangements.words(inflection))

    def insert(self, phrase: Word, item, index: int) -> Word:
        """`phrase` with `item` at `index` of its arrangement, counted without `item`."""
        return replace(phrase, arrangement=self.arrangements.insert(phrase.arrangement, item, index))

    def find(self, playmat, id):
        """The word with this id, whether placed directly or as an adjective, else None."""
        for word in playmat:
            if word.id == id:
                return word
            for item in word.arrangement:
                if isinstance(item, Word) and item.id == id:
                    return item
        return None

    def owner(self, playmat, id):
        """The noun phrase that has the word with this id as an adjective, else None."""
        for word in playmat:
            if any(isinstance(item, Word) and item.id == id for item in word.arrangement):
                return word
        return None

    def without(self, playmat, id) -> tuple[Word, ...]:
        """The playmat with the word of this id removed, wherever it was."""
        return tuple(
            replace(word, arrangement=tuple(item for item in word.arrangement
                                            if not (isinstance(item, Word) and item.id == id)))
            for word in playmat if word.id != id
        )

    def without_slot(self, playmat, phrase: int, slot: Slot) -> tuple[Word, ...]:
        return tuple(replace(word, arrangement=self.arrangements.remove(word.arrangement, slot))
                     if word.id == phrase else word
                     for word in playmat)

    def replaced(self, playmat, word: Word) -> tuple[Word, ...]:
        return tuple(word if item.id == word.id else item for item in playmat)

    def reinflect(self, playmat, id, inflection) -> tuple[Word, ...]:
        """The playmat with the word of this id given the `Rule` tree `inflection`."""
        def visit(word):
            if word.id == id:
                return self.reinflected(word, inflection)
            return replace(word, arrangement=tuple(visit(item) if isinstance(item, Word) else item
                                                   for item in word.arrangement))
        return tuple(visit(word) for word in playmat)

    def tokens(self, playmat) -> tuple[str, ...]:
        """The statement's words as the player arranged them."""
        result = []
        for word in playmat:
            if word.inflection.tag == 'np':
                result += [text for _, text in self.items(word)]
            else:
                result += [text for _, text in self.arrangements.words(word.inflection)]
        return tuple(result)

    def statement(self, playmat) -> tuple:
        """The statement as the player arranged it: a `Rule` tree for each word on the playmat."""
        return tuple(self.arrangements.ordered(word.arrangement, word.inflection) if word.inflection.tag == 'np'
                     else word.inflection
                     for word in playmat)
