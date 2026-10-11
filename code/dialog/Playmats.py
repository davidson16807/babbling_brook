"""Arrows on the playmat: the statement the player composes, and the words placed on it.

A playmat is a tuple of `Word`s. A word is a lexeme with the text of one of its
inflections; a noun phrase also has an arrangement, whose adjectives are words too.
"""
from dataclasses import replace

from .DialogState import Slot, Word


class Playmats:
    """
    `Playmats` is a category whose objects are playmats and the words on them, and
    whose arrows place, find, move, reinflect, and remove words, and read a playmat
    as the words of its statement. It is built from `Arrangements`, for the order
    within each noun phrase, and `ListTrees`, which reads the list tree of each
    word's inflection; `inflections` (lexeme → text → list tree) and
    `default_inflections` (lexeme → text) give each lexeme's inflections.
    """
    def __init__(self, arrangements, list_trees, inflections, default_inflections):
        self.arrangements = arrangements
        self.list_trees = list_trees
        self.inflections = inflections
        self.default_inflections = default_inflections

    def inflection_texts(self, lexeme) -> list[str]:
        """The texts of every inflection of `lexeme`, which its grid offers."""
        return list(self.inflections[lexeme])

    def tree(self, word):
        return self.inflections[word.lexeme][word.inflection]

    def is_phrase(self, word) -> bool:
        return self.arrangements.is_phrase(self.tree(word))

    def is_adjective(self, word) -> bool:
        return self.arrangements.is_adjective(self.tree(word))

    def placed(self, lexeme: str, id: int) -> Word:
        """A newly placed word, with its lexeme's default inflection."""
        word = Word(id, lexeme, self.default_inflections[lexeme])
        return replace(word, arrangement=self.arrangements.slots(self.tree(word))) if self.is_phrase(word) else word

    def reinflected(self, word, text: str) -> Word:
        """`word` with the inflection `text`; a phrase keeps the player's order where it can."""
        word = replace(word, inflection=text)
        return replace(word, arrangement=self.arrangements.arrange(word.arrangement, self.tree(word))) \
            if self.is_phrase(word) else word

    def items(self, word) -> list[tuple[object, str]]:
        """(slot or adjective, text) for each item of a noun phrase, in the player's order."""
        return self.arrangements.items(word.arrangement, self.tree(word))

    def slot_text(self, word, slot: Slot) -> str:
        return self.arrangements.texts(self.tree(word))[slot]

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

    def reinflect(self, playmat, id, text: str) -> tuple[Word, ...]:
        """The playmat with the word of this id given the inflection `text`."""
        def visit(word):
            if word.id == id:
                return self.reinflected(word, text)
            return replace(word, arrangement=tuple(visit(item) if isinstance(item, Word) else item
                                                   for item in word.arrangement))
        return tuple(visit(word) for word in playmat)

    def tokens(self, playmat) -> tuple[str, ...]:
        """The statement's words as the player arranged them."""
        result = []
        for word in playmat:
            if self.is_phrase(word):
                result += [text for _, text in self.items(word)]
            else:
                result += [text for _, text in self.list_trees.words(self.tree(word))]
        return tuple(result)
