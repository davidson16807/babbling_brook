"""Group generated inflections by their text: the bundle text → tagpoints.

`InflectionGeneration` maps each tagpoint to tokens. A text the player picks may
have come from several tagpoints (English "give"), so a `Lexeme` keeps, for each
distinct text, every tagpoint that renders to it.
"""
from ..model.Lexicon import Inflection, Lexeme, tagpoint


def bundle(generated) -> dict:
    """tokens → tagpoints, from (tags, tokens) pairs, in first-generated order."""
    fibers = {}
    for tags, tokens in generated:
        if tokens:
            fibers.setdefault(tokens, []).append(tagpoint(tags))
    return fibers


def lexeme(id, part, generated, default, listing=None) -> Lexeme:
    """A lexeme from (tags, tokens) pairs.

    `default` is a DictSet that selects the inflection a newly placed word starts
    with, the first one whose tags it contains. The inventory shows that
    inflection, or, given a `listing` DictSet, the first three texts it selects
    (as in "I, you, he…").
    """
    generated = list(generated)
    text = lambda tokens: ' '.join(token.text for token in tokens)
    defaults = [tokens for tags, tokens in generated if tokens and tags in default]
    if not defaults:
        raise ValueError(f'{default.name} selects no inflection of {id!r}')
    inflections = tuple(Inflection(tokens, tuple(points)) for tokens, points in bundle(generated).items())
    if listing is None:
        display = text(defaults[0])
    else:
        listed = list(dict.fromkeys(tokens for tags, tokens in generated if tokens and tags in listing))
        display = ', '.join(text(tokens) for tokens in listed[:3]) + '…'
    return Lexeme(id, part, display, text(defaults[0]), inflections)
