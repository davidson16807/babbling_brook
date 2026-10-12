"""English MVP lexicon and noun-phrase inflection generation.

The constructors deliberately consume/produce ``DictStore`` tagpoints and
bundle duplicate visible strings.  A future Spanish adapter can therefore feed
the output of ``InflectionGeneration`` through the same ``bundle`` function.
"""
from __future__ import annotations

from collections import defaultdict

from .DialogState import DictStore, Inflection, Lexeme, NounPhraseItem, PhraseToken


def bundle(rows) -> tuple[Inflection, ...]:
    """Invert ``tagpoint -> text`` into unique ``text -> tagpoints`` bundles."""
    grouped = defaultdict(list)
    for tagpoint, text in rows:
        if text and tagpoint not in grouped[text]:
            grouped[text].append(tagpoint)
    return tuple(Inflection(text, tuple(tagpoints)) for text, tagpoints in grouped.items())


def _forms(part_of_speech, term, rows):
    return bundle((DictStore.of({'part-of-speech': part_of_speech, 'term': term}, **tags), text)
                  for text, tags in rows)


def english_lexicon() -> tuple[Lexeme, ...]:
    entries = (
        Lexeme('ball', 'ball', 'noun', 'ball', _forms('noun', 'ball', (
            ('ball', {'number': 'singular'}), ('balls', {'number': 'plural'})))),
        Lexeme('boy', 'boy', 'noun', 'boy', _forms('noun', 'boy', (
            ('boy', {'number': 'singular'}), ('boys', {'number': 'plural'})))),
        Lexeme('give', 'give', 'verb', 'give', _forms('verb', 'give', (
            ('give', {'tense': 'present', 'person': 'non-third-singular'}),
            ('gives', {'tense': 'present', 'person': 'third-singular'}),
            ('gave', {'tense': 'past', 'person': 'any'})))),
        Lexeme('house', 'house', 'noun', 'house', _forms('noun', 'house', (
            ('house', {'number': 'singular'}), ('houses', {'number': 'plural'})))),
        Lexeme('person', 'person', 'pronoun', 'I', _forms('pronoun', 'person', (
            ('I', {'person': 'first', 'number': 'singular', 'case': 'subject'}),
            ('you', {'person': 'second', 'number': 'singular', 'case': 'subject'}),
            ('he', {'person': 'third', 'number': 'singular', 'gender': 'masculine', 'case': 'subject'}),
            ('she', {'person': 'third', 'number': 'singular', 'gender': 'feminine', 'case': 'subject'}),
            ('we', {'person': 'first', 'number': 'plural', 'case': 'subject'}),
            ('they', {'person': 'third', 'number': 'plural', 'case': 'subject'})))),
        Lexeme('red', 'red', 'adjective', 'red', _forms('adjective', 'red', (
            ('red', {'degree': 'positive'}),))),
        Lexeme('talk', 'talk', 'verb', 'talk', _forms('verb', 'talk', (
            ('talk', {'tense': 'present', 'person': 'non-third-singular'}),
            ('talks', {'tense': 'present', 'person': 'third-singular'}),
            ('talked', {'tense': 'past', 'person': 'any'})))),
        Lexeme('walk', 'walk', 'verb', 'walk', _forms('verb', 'walk', (
            ('walk', {'tense': 'present', 'person': 'non-third-singular'}),
            ('walks', {'tense': 'present', 'person': 'third-singular'}),
            ('walked', {'tense': 'past', 'person': 'any'})))),
    )
    return tuple(sorted(entries, key=lambda item: item.canonical.casefold()))


def phrase_options(phrase: NounPhraseItem, lexemes: tuple[Lexeme, ...]):
    """Return de-duplicated English phrase tokenizations and their tagpoints."""
    by_id = {lexeme.id: lexeme for lexeme in lexemes}
    noun = by_id[phrase.noun_lexeme_id]
    adjectives = [token for token in phrase.tokens if token.role == 'adjective']
    rows = []
    for noun_form in noun.inflections:
        number = noun_form.tagpoints[0].get('number')
        determiners = (('', {}), ('the', {'definiteness': 'definite'}))
        if number == 'singular':
            determiners += (('a', {'definiteness': 'indefinite'}),)
        for adposition, role in (('', 'object'), ('to', 'indirect-object')):
            for determiner, det_tags in determiners:
                tokens = []
                if adposition:
                    tokens.append(PhraseToken('adposition', adposition, None,
                                              (DictStore.of({'role': role}),)))
                if determiner:
                    tokens.append(PhraseToken('determiner', determiner, None,
                                              (DictStore.of(det_tags),)))
                tokens.extend(adjectives)
                tokens.append(PhraseToken('noun', noun_form.text, noun.id, noun_form.tagpoints))
                text = ' '.join(token.text for token in tokens)
                rows.append((text, tuple(tokens)))
    # Surface duplicates are possible with richer languages. Preserve the first
    # tokenization; each token still retains every interpretation of its text.
    unique = {}
    for text, tokens in rows:
        unique.setdefault(text, tokens)
    return tuple(unique.items())


def default_phrase(item_id: int, noun: Lexeme) -> NounPhraseItem:
    form = noun.inflections[0]
    return NounPhraseItem(item_id, noun.id, (
        PhraseToken('determiner', 'the', None,
                    (DictStore.of({'definiteness': 'definite'}),)),
        PhraseToken('noun', form.text, noun.id, form.tagpoints),
    ))
