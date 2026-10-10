"""Pure operations on playmat words and noun-phrase sequences."""
from dataclasses import replace

from ..model.Lexicon import Inflection, Token
from .DialogState import Modifier, Word


def phrase_sequence(inflection: Inflection, modifiers) -> list:
    """Interleave a phrase's generated tokens with its adjectives, in display order.

    Items are `Token`s (articles, adpositions, the noun) and `Modifier`s.
    Offsets beyond the available tokens are clamped to the phrase's ends.
    """
    tokens = inflection.tokens
    head = inflection.head
    before, noun, after = tokens[:head], tokens[head], tokens[head + 1:]
    def gap(offset):
        return (max(offset, -(len(before) + 1)) if offset < 0
                else min(max(offset, 1), len(after) + 1))
    gaps = [gap(modifier.offset) for modifier in modifiers]
    def at(offset):
        return [modifier for modifier, g in zip(modifiers, gaps) if g == offset]
    sequence = []
    for k, token in enumerate(before):
        sequence += [*at(-(len(before) + 1 - k)), token]
    sequence += [*at(-1), noun]
    for k, token in enumerate(after):
        sequence += [*at(k + 1), token]
    return sequence + at(len(after) + 1)


def sequence_modifiers(sequence, head: int) -> tuple[Modifier, ...]:
    """Inverse of `phrase_sequence`: recompute every adjective's offset from its position."""
    generated = [index for index, item in enumerate(sequence) if isinstance(item, Token)]
    noun = generated[head]
    modifiers = []
    for index, item in enumerate(sequence):
        if isinstance(item, Modifier):
            if index < noun:
                offset = -(1 + sum(1 for j in generated if index < j < noun))
            else:
                offset = 1 + sum(1 for j in generated if noun < j < index)
            modifiers.append(replace(item, offset=offset))
    return tuple(modifiers)


def find(playmat, id):
    """The word with this id, whether placed directly or as a modifier, else None."""
    for word in playmat:
        if word.id == id:
            return word
        for modifier in word.modifiers:
            if modifier.word.id == id:
                return modifier.word
    return None


def owner(playmat, id):
    """The noun phrase that has the word with this id as a modifier, else None."""
    for word in playmat:
        if any(modifier.word.id == id for modifier in word.modifiers):
            return word
    return None


def without(playmat, id) -> tuple[Word, ...]:
    """The playmat with the word of this id removed, wherever it was."""
    return tuple(
        replace(word, modifiers=tuple(m for m in word.modifiers if m.word.id != id))
        for word in playmat if word.id != id
    )


def reinflect(playmat, id, inflection: str) -> tuple[Word, ...]:
    def visit(word):
        if word.id == id:
            return replace(word, inflection=inflection)
        return replace(word, modifiers=tuple(replace(m, word=visit(m.word)) for m in word.modifiers))
    return tuple(visit(word) for word in playmat)


def insert_modifier(phrase: Word, inflection: Inflection, word: Word, index: int) -> Word:
    """Place `word` at `index` of the phrase's display sequence (without `word`)."""
    modifiers = tuple(m for m in phrase.modifiers if m.word.id != word.id)
    sequence = phrase_sequence(inflection, modifiers)
    sequence.insert(max(0, min(index, len(sequence))), Modifier(word, -1))
    return replace(phrase, modifiers=sequence_modifiers(sequence, inflection.head))


def describe(playmat, lexicon) -> str:
    """The statement and every word's number of interpretations, for logs and debugging."""
    def line(word, indent):
        count = len(lexicon.lexemes[word.lexeme].inflection(word.inflection).tagpoints)
        return f'{indent}{word.inflection:24} {word.lexeme:10} {count} interpretation{"s" * (count != 1)}'
    lines = [' '.join(tokens(playmat, lexicon))]
    for word in playmat:
        lines.append(line(word, '  '))
        lines += [line(modifier.word, '    ') for modifier in word.modifiers]
    return '\n'.join(lines)


def tokens(playmat, lexicon) -> tuple[str, ...]:
    """The statement's words as the player arranged them."""
    texts = []
    for word in playmat:
        lexeme = lexicon.lexemes[word.lexeme]
        if not lexeme.is_noun_phrase:
            texts += [token.text for token in lexeme.inflection(word.inflection).tokens]
            continue
        for item in phrase_sequence(lexeme.inflection(word.inflection), word.modifiers):
            texts.append(item.text if isinstance(item, Token) else item.word.inflection)
    return tuple(texts)
