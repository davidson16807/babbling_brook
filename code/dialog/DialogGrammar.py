"""Validate selected tagpoint bundles and player order; never parse player text."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DialogCommand:
    action: str
    actor: object  # DictList
    verb: object  # DictList of compatible inflections
    object: object = None  # DictList
    target: object = None  # DictList
    modifiers: tuple = ()  # (word id, adjective DictList) pairs


class DialogGrammar:
    def __init__(self, language):
        self.language = language

    @staticmethod
    def agrees(adjective, noun):
        return ((adjective.get('degree') != 'superlative' or noun['definiteness'] == 'definite')
                and all(adjective.get(axis) == noun.get(axis) for axis in ('number', 'gender', 'case')
                        if axis in adjective and axis in noun))

    def _phrase(self, word, relations):
        language = self.language
        if not word.pieces:
            return ()
        ranks = [language.noun_order.index(p.kind) for p in word.pieces]
        if ranks != sorted(ranks):
            return ()
        adjective_ranks = [language.adjective_order[p.word.lexeme] for p in word.pieces if p.word]
        if adjective_ranks != sorted(adjective_ranks):
            return ()
        candidates = [t for t in language.points(word.inflection) if t['relation'] in relations]
        # Agreement is existential over each selected surface's entire bundle.
        # No first-tagpoint shortcut: e.g. "you" and "give" have many readings.
        return tuple(t for t in candidates if all(
            any(self.agrees(a, t)
                for a in language.points(p.word.inflection))
            for p in word.pieces if p.word))

    def validate(self, state):
        language = self.language
        words = state.words
        if len(words) < 2 or language.lexemes[words[1].lexeme].kind != 'verb':
            return None
        actor, verb, *arguments = words
        subjects = self._phrase(actor, {'subject'})
        verbs = language.points(verb.inflection)
        matches = [(s, v) for s in subjects for v in verbs
                   if all(s[axis] == v[axis] for axis in ('person', 'number'))]
        if not matches:
            return None
        action = verb.lexeme
        obj = target = None
        if action == 'give':
            if len(arguments) != 2:
                return None
            obj = self._phrase(arguments[0], {'object'})
            target = self._phrase(arguments[1], {'recipient'})
            if not obj or not target:
                return None
        elif action in ('walk', 'talk'):
            if len(arguments) > 1:
                return None
            if arguments:
                relations = {'destination', 'interior', 'surface', 'company'} if action == 'walk' else {'recipient', 'company'}
                target = self._phrase(arguments[0], relations)
                if not target:
                    return None
        else:
            return None
        # Preserve all locally compatible interpretations. Modifier stores are
        # returned with the command for a future world-command resolver.
        def unique(points):
            return list({tuple(sorted(p.items())): p for p in points}.values())
        contexts = [(actor, unique(s for s, _ in matches))]
        if obj:
            contexts.append((arguments[0], obj))
        if target:
            contexts.append((arguments[-1], target))
        modifiers = tuple((w.id, language.store(p.word.lexeme,
                          [a for a in language.points(p.word.inflection)
                           if any(self.agrees(a, t) for t in candidates)]))
                          for w, candidates in contexts for p in w.pieces if p.word)
        return DialogCommand(
            action, language.store('actor', unique(s for s, _ in matches)),
            language.store('verb', unique(v for _, v in matches)),
            language.store('object', obj) if obj else None,
            language.store('target', target) if target else None,
            modifiers)
