"""Pure operations on playmat words and noun-phrase arrangements.

A noun phrase's `arrangement` is its words in the player's order: a `Slot` for
each token of its inflection (article, adposition, noun, ...) and a `Word` for
each adjective. The player orders all of them; nothing here reorders them.
"""
from dataclasses import replace

from .DialogState import Slot, Word


def slots(inflection) -> tuple[Slot, ...]:
    """A slot per token of `inflection`, in the order the language produced them."""
    counts, result = {}, []
    for token in inflection.tokens:
        result.append(Slot(token.part, counts.get(token.part, 0)))
        counts[token.part] = counts.get(token.part, 0) + 1
    return tuple(result)


def texts(inflection) -> dict[Slot, str]:
    return dict(zip(slots(inflection), (token.text for token in inflection.tokens)))


def arrange(arrangement, inflection) -> tuple:
    """`arrangement` after the phrase takes `inflection`.

    Slots the inflection keeps, and every adjective, stay where the player put
    them; slots it lacks are dropped. A slot it adds is inserted where the
    language put that token, counting from the front of the phrase.
    """
    wanted = slots(inflection)
    result = [item for item in arrangement if isinstance(item, Word) or item in wanted]
    for index, slot in enumerate(wanted):
        if slot not in result:
            result.insert(min(index, len(result)), slot)
    return tuple(result)


def placed(lexeme, id: int) -> Word:
    """A newly placed word, with its default inflection."""
    word = Word(id, lexeme.id, lexeme.default)
    if lexeme.is_noun_phrase:
        word = replace(word, arrangement=slots(lexeme.inflection(lexeme.default)))
    return word


def phrase_items(word, inflection) -> list[tuple[object, str]]:
    """(slot or adjective, text) for each word of a noun phrase, in the player's order."""
    words = texts(inflection)
    return [(item, words[item] if isinstance(item, Slot) else item.inflection)
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


def reinflect(playmat, id, text: str, lexicon) -> tuple[Word, ...]:
    """The playmat with the word of this id given the inflection `text`."""
    def visit(word):
        if word.id == id:
            lexeme = lexicon.lexemes[word.lexeme]
            arrangement = (arrange(word.arrangement, lexeme.inflection(text))
                           if lexeme.is_noun_phrase else word.arrangement)
            return replace(word, inflection=text, arrangement=arrangement)
        return replace(word, arrangement=tuple(visit(item) if isinstance(item, Word) else item
                                               for item in word.arrangement))
    return tuple(visit(word) for word in playmat)


def describe(playmat, lexicon) -> str:
    """The statement and every word's number of interpretations, for logs and debugging."""
    def line(word, indent):
        count = len(lexicon.lexemes[word.lexeme].inflection(word.inflection).tagpoints)
        return f'{indent}{word.inflection:24} {word.lexeme:10} {count} interpretation{"s" * (count != 1)}'
    lines = [' '.join(tokens(playmat, lexicon))]
    for word in playmat:
        lines.append(line(word, '  '))
        lines += [line(item, '    ') for item in word.arrangement if isinstance(item, Word)]
    return '\n'.join(lines)


def tokens(playmat, lexicon) -> tuple[str, ...]:
    """The statement's words as the player arranged them."""
    result = []
    for word in playmat:
        lexeme = lexicon.lexemes[word.lexeme]
        inflection = lexeme.inflection(word.inflection)
        if lexeme.is_noun_phrase:
            result += [text for _, text in phrase_items(word, inflection)]
        else:
            result += [token.text for token in inflection.tokens]
    return tuple(result)
