"""Arrows on the playmat: the statement the player composes, and the words placed on it.

A playmat is a tuple of `Word`s, each a lexeme with one of its inflections as a `Rule`
tree; a noun phrase also has the children the player added to it, and the order of
all its children (see Arrangements.py). What leaves the dialog is `statement`, a
`Rule` tree per word in the player's order.
"""
from dataclasses import replace

from .DialogState import Word


class Playmats:
    """
    `Playmats` is a category whose objects are playmats and the words on them, and
    whose arrows place, find, move, reinflect, and remove words, and read a playmat
    as the words or the `Rule` trees of its statement. It is built from
    `Arrangements`, for each noun phrase and the reading of `Rule`s.
    """
    def __init__(self, arrangements):
        self.arrangements = arrangements

    def placed(self, lexeme: str, inflection, id: int) -> Word:
        """A newly placed word of `lexeme`, with the `Rule` tree `inflection`."""
        word = Word(id, lexeme, inflection)
        return self.arrangements.arranged(word) if inflection.tag == 'np' else word

    def reinflected(self, word, inflection) -> Word:
        """`word` with the `Rule` tree `inflection`; a phrase keeps the player's order where it can."""
        return (self.arrangements.reinflected(word, inflection) if inflection.tag == 'np'
                else replace(word, inflection=inflection))

    def text(self, word) -> str:
        """What `word` reads as, with a phrase's words in the player's order."""
        return ' '.join(self.tokens((word,)))

    def index(self, options, inflection) -> int:
        """The index of the option among `options` that reads as `inflection`, word for word."""
        return [self.arrangements.words(option) for option in options].index(self.arrangements.words(inflection))

    def find(self, playmat, id):
        """The word with this id, else None."""
        return next((word for word in playmat if word.id == id), None)

    def without(self, playmat, id) -> tuple[Word, ...]:
        return tuple(word for word in playmat if word.id != id)

    def inserted(self, playmat, word, index: int) -> tuple[Word, ...]:
        """The playmat with `word` at `index`, counted without it."""
        playmat = self.without(playmat, word.id)
        return (*playmat[:index], word, *playmat[index:])

    def replaced(self, playmat, word: Word) -> tuple[Word, ...]:
        return tuple(word if item.id == word.id else item for item in playmat)

    def tokens(self, playmat) -> tuple[str, ...]:
        """The statement's words as the player arranged them."""
        result = []
        for word in playmat:
            if word.inflection.tag == 'np':
                result += [text for _, text in self.arrangements.items(word)]
            else:
                result += [text for _, text in self.arrangements.words(word.inflection)]
        return tuple(result)

    def statement(self, playmat) -> tuple:
        """The statement as the player arranged it: a `Rule` tree for each word on the playmat."""
        return tuple(self.arrangements.ordered(word) if word.inflection.tag == 'np' else word.inflection
                     for word in playmat)
