"""Small, deterministic English grammar used by the dialog MVP."""
from __future__ import annotations

from dataclasses import dataclass

from .DialogState import NounPhraseItem, WordItem


@dataclass(frozen=True, slots=True)
class DialogMeaning:
    subject: str
    verb: str
    objects: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class DialogResult:
    valid: bool
    text: str
    meaning: DialogMeaning | None = None


class DialogValidator:
    def _reading(self, item, **wanted):
        return next((tagpoint for tagpoint in item.tagpoints
                     if all(tagpoint.get(key) == value for key, value in wanted.items())), None)

    def _phrase(self, state, phrase, required_role):
        roles = tuple(token.role for token in phrase.tokens)
        if not roles or roles[-1] != 'noun':
            return None
        prefix = ('adposition',) if required_role == 'indirect-object' else ()
        if required_role == 'object' and roles[0] == 'adposition':
            return None
        if required_role == 'indirect-object' and (roles[0] != 'adposition' or phrase.tokens[0].text != 'to'):
            return None
        core = roles[len(prefix):]
        if core and core[0] == 'determiner':
            core = core[1:]
        if any(role != 'adjective' for role in core[:-1]) or core[-1:] != ('noun',):
            return None
        noun = phrase.tokens[-1]
        number = noun.tagpoints[0].get('number')
        determiners = [token.text for token in phrase.tokens if token.role == 'determiner']
        if number == 'singular' and not determiners:
            return None
        if 'a' in determiners and number != 'singular':
            return None
        return state.lexeme(phrase.noun_lexeme_id).term

    def validate(self, state):
        items = state.playmat
        if len(items) < 2 or not all(isinstance(item, WordItem) for item in items[:2]):
            return DialogResult(False, 'What? Start with a speaker and an action.')
        subject, verb = items[:2]
        subject_lexeme, verb_lexeme = state.lexeme(subject.lexeme_id), state.lexeme(verb.lexeme_id)
        if subject_lexeme.part_of_speech != 'pronoun' or verb_lexeme.part_of_speech != 'verb':
            return DialogResult(False, 'What? English puts the speaker before the action here.')
        subject_tags = subject.tagpoints[0]
        third_singular = subject_tags.get('person') == 'third' and subject_tags.get('number') == 'singular'
        agreement = 'third-singular' if third_singular else 'non-third-singular'
        if (self._reading(verb, tense='present', person=agreement) is None
                and self._reading(verb, tense='past', person='any') is None):
            return DialogResult(False, 'What? The action does not agree with the speaker.')

        expected = {'walk': (), 'talk': ('indirect-object',),
                    'give': ('object', 'indirect-object')}[verb_lexeme.term]
        rest = items[2:]
        if len(rest) != len(expected) or not all(isinstance(item, NounPhraseItem) for item in rest):
            return DialogResult(False, f'What? “{verb_lexeme.term}” needs {len(expected)} noun phrase(s).')
        objects = []
        for phrase, role in zip(rest, expected):
            term = self._phrase(state, phrase, role)
            if term is None:
                return DialogResult(False, 'What? Check the noun phrase word order and agreement.')
            objects.append((role, term))
        sentence = ' '.join(
            item.text if isinstance(item, WordItem) else ' '.join(token.text for token in item.tokens)
            for item in items)
        meaning = DialogMeaning(subject.text, verb_lexeme.term, tuple(objects))
        return DialogResult(True, f'You said: “{sentence}.”', meaning)
