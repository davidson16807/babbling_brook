"""Pure operations on playmat words and noun-phrase arrangements.

`inflections` is lexeme → text → list tree, as `inflection/english.py` computes it;
a lexeme's first inflection is the one it is placed with. A noun phrase's
`arrangement` is its words in the player's order: a `Slot` for each word of its
inflection (article, adposition, noun, ...) and a `Word` for each adjective. The
player orders all of them; nothing here reorders them.
"""
from dataclasses import replace

from ..inflection.listtrees import kind, words
from .DialogState import Slot, Word


def is_phrase(tree) -> bool:
    return kind(tree) == 'np'


def slots(tree) -> tuple[Slot, ...]:
    """A slot per word of the list tree, in the order the language produced them."""
    counts, result = {}, []
    for part, _ in words(tree):
        result.append(Slot(part, counts.get(part, 0)))
        counts[part] = counts.get(part, 0) + 1
    return tuple(result)


def texts(tree) -> dict[Slot, str]:
    return dict(zip(slots(tree), (text for _, text in words(tree))))


def arrange(arrangement, tree) -> tuple:
    """`arrangement` after the phrase takes the inflection `tree`.

    Slots the inflection keeps, and every adjective, stay where the player put
    them; slots it lacks are dropped. A slot it adds is inserted where the
    language put that word, counting from the front of the phrase.
    """
    wanted = slots(tree)
    result = [item for item in arrangement if isinstance(item, Word) or item in wanted]
    for index, slot in enumerate(wanted):
        if slot not in result:
            result.insert(min(index, len(result)), slot)
    return tuple(result)


def placed(lexeme: str, inflections, id: int) -> Word:
    """A newly placed word, with its lexeme's first inflection."""
    text, tree = next(iter(inflections[lexeme].items()))
    return Word(id, lexeme, text, slots(tree) if is_phrase(tree) else ())


def phrase_items(word, tree) -> list[tuple[object, str]]:
    """(slot or adjective, text) for each word of a noun phrase, in the player's order."""
    slot_texts = texts(tree)
    return [(item, slot_texts[item] if isinstance(item, Slot) else item.inflection)
            for item in word.arrangement]


def find(playmat, id):
    """The word with this id, whether placed directly or as an adjective, else None."""
    for word in playmat:
        if word.id == id:
            return word
        for item in word.arrangement:
            if isinstance(item, Word) and item.id == id:
                return item
    return None


def owner(playmat, id):
    """The noun phrase that has the word with this id as an adjective, else None."""
    for word in playmat:
        if any(isinstance(item, Word) and item.id == id for item in word.arrangement):
            return word
    return None


def remove_item(arrangement, item) -> tuple:
    if isinstance(item, Slot):
        return tuple(other for other in arrangement if other != item)
    return tuple(other for other in arrangement if not (isinstance(other, Word) and other.id == item.id))


def insert_item(phrase: Word, item, index: int) -> Word:
    """Place `item` at `index` of the phrase's arrangement (counted without `item`)."""
    arrangement = list(remove_item(phrase.arrangement, item))
    arrangement.insert(max(0, min(index, len(arrangement))), item)
    return replace(phrase, arrangement=tuple(arrangement))


def without(playmat, id) -> tuple[Word, ...]:
    """The playmat with the word of this id removed, wherever it was."""
    return tuple(
        replace(word, arrangement=tuple(item for item in word.arrangement
                                        if not (isinstance(item, Word) and item.id == id)))
        for word in playmat if word.id != id
    )


def without_slot(playmat, phrase: int, slot: Slot) -> tuple[Word, ...]:
    return tuple(replace(word, arrangement=remove_item(word.arrangement, slot)) if word.id == phrase else word
                 for word in playmat)


def replaced(playmat, word: Word) -> tuple[Word, ...]:
    return tuple(word if item.id == word.id else item for item in playmat)


def reinflect(playmat, id, text: str, inflections) -> tuple[Word, ...]:
    """The playmat with the word of this id given the inflection `text`."""
    def visit(word):
        if word.id == id:
            tree = inflections[word.lexeme][text]
            arrangement = arrange(word.arrangement, tree) if is_phrase(tree) else word.arrangement
            return replace(word, inflection=text, arrangement=arrangement)
        return replace(word, arrangement=tuple(visit(item) if isinstance(item, Word) else item
                                               for item in word.arrangement))
    return tuple(visit(word) for word in playmat)


def tokens(playmat, inflections) -> tuple[str, ...]:
    """The statement's words as the player arranged them."""
    result = []
    for word in playmat:
        tree = inflections[word.lexeme][word.inflection]
        if is_phrase(tree):
            result += [text for _, text in phrase_items(word, tree)]
        else:
            result += [text for _, text in words(tree)]
    return tuple(result)
