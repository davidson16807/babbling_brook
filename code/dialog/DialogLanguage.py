"""English MVP, generated from upstream DictSpaces through RuleLanguage.

All imports of the external library happen through LanguagesLibrary. No pygame,
manual sentence translations, random state, or GUI state lives here. Upstream
stores are treated as immutable after construction.
"""
from dataclasses import dataclass

from ..adapter.LanguagesLibrary import LanguagesLibrary
from ..inflection.InflectionGeneration import InflectionGeneration


@dataclass(frozen=True)
class DialogLexeme:
    key: str
    kind: str
    label: str
    canonical: str
    forms: object  # DictLookup: tagpoint -> visible text
    bundle: dict   # visible text -> list of ALL tagpoints
    parts: dict    # visible text -> tuple[(rule tag, token text), ...]


class DialogLanguage:
    code = 'en'
    substitutions = ()
    noun_order = ('adposition', 'det', 'adj', 'n')
    adjective_order = {'small': 0, 'tall': 0, 'red': 1}

    def __init__(self, directory=None):
        library = LanguagesLibrary(directory)
        english = library.import_module('languages.english')
        stores = library.import_module('tools.dictstores')
        indexing = library.import_module('tools.indexing')
        inflections = library.import_module('tools.inflections')
        self.Rule = library.import_module('tools.nodes').Rule
        self.DictList = stores.DictList
        self.DictLookup = stores.DictLookup
        self.DictSpace = stores.DictSpace
        self.Indexing = indexing.DictTupleIndexing
        rule_language = library.import_module('babbling_brook.inflection.RuleLanguage').RuleLanguage
        self.defaults = {**inflections.tag_defaults, 'script': 'latin', 'aspect': 'simple',
                         'case': 'nominative', 'role': 'agent', 'motion': 'associated',
                         'show-gender': False, 'language-type': 'foreign'}
        language = english.english_language
        self.rules = rule_language(language.semantics, language.grammar, self.defaults,
                                   english.list_tools, language.substitutions)
        self.lexemes = {}
        for noun in ('ball', 'boy', 'house'):
            self._noun(noun)
        self._noun('person', personal=True)
        for verb in ('give', 'talk', 'walk'):
            self._verb(verb)
        for adjective in ('red', 'small', 'tall'):
            self._adjective(adjective)
        self.inventory = tuple(sorted(self.lexemes, key=lambda k: self.lexemes[k].label.casefold()))

    def store(self, name, points):
        points = list(points)
        keys = sorted(points[0]) if points else []
        return self.DictList(name, self.Indexing(keys), points)

    @staticmethod
    def points(store):
        return tuple(store.indexing.dictkey(key) for key in store)

    def _space(self, name, axes):
        return self.DictSpace(name, self.Indexing(sorted(axes)), axes)

    def _parts(self, tree):
        if isinstance(tree, self.Rule):
            if tree.tag in ('n', 'v', 'adj', 'det', 'adposition'):
                words = self._text(tree.content)
                return [(tree.tag, words)] if words else []
            return self._parts(tree.content)
        if isinstance(tree, list):
            return [part for child in tree for part in self._parts(child)]
        text = self._text(tree)
        return [('v', text)] if text else []

    def _text(self, tree):
        if isinstance(tree, self.Rule):
            return self._text(tree.content)
        if isinstance(tree, list):
            return ' '.join(filter(None, (self._text(t) for t in tree)))
        if tree is None:
            raise ValueError('The language generator returned a missing inflection')
        return ' '.join(str(tree).replace('∅', '').split())

    def _generate(self, key, kind, axes, tree, canonical, label=None, predicate=lambda t: True,
                  traversal=None):
        traversal = self._space(key, axes) if traversal is None else traversal
        def demonstration(tags, templates):
            return self.rules.map(['selected', tree(tags)], 'latin', semes={'selected': tags})
        forms = self.DictLookup(key, traversal.indexing)
        bundles, parts = {}, {}
        for tags, trees in InflectionGeneration().generate([demonstration], traversal):
            if not predicate(tags):
                continue
            pieces = tuple(self._parts(trees))
            text = ' '.join(p[1] for p in pieces)
            if not text or any(c in text for c in '[]❕❔—'):
                continue
            forms[tags] = text
            bundles.setdefault(text, []).append(tags)
            parts.setdefault(text, pieces)
        if canonical not in bundles:
            raise ValueError(f'Missing canonical form for {key}: {canonical!r}')
        self.lexemes[key] = DialogLexeme(key, kind, label or canonical, canonical, forms, bundles, parts)

    def _noun(self, noun, personal=False):
        # The relation is an internal traversal selector, never a player label.
        relations = {
            'subject': {'subjectivity': 'subject', 'role': 'agent', 'motion': 'associated'},
            'object': {'subjectivity': 'direct-object', 'role': 'patient', 'motion': 'associated'},
            'recipient': {'subjectivity': 'indirect-object', 'role': 'possessor', 'motion': 'acquired'},
            'destination': {'subjectivity': 'adverbial', 'role': 'location', 'motion': 'acquired'},
            'interior': {'subjectivity': 'adverbial', 'role': 'interior', 'motion': 'associated'},
            'surface': {'subjectivity': 'adverbial', 'role': 'surface', 'motion': 'associated'},
            'company': {'subjectivity': 'adverbial', 'role': 'company', 'motion': 'associated'},
        }
        axes = {'noun': noun, 'noun-form': 'personal' if personal else 'common',
                'number': ['singular', 'plural'],
                'person': ['1', '2', '3'] if personal else '3',
                'gender': ['masculine', 'feminine', 'neuter'] if personal else 'masculine' if noun == 'boy' else 'neuter',
                'definiteness': ['adefinite'] if personal else ['definite', 'indefinite', 'adefinite'],
                'relation': list(relations)}
        # Relations must be actual tags in the DictStore, not inferred from text.
        traversal = self._space(noun, axes)
        points = []
        for key in traversal:
            point = traversal.indexing.dictkey(key)
            points.append({**point, **relations[point['relation']],
                           'case': 'nominative' if point['relation'] == 'subject' else 'oblique'})
        def tree(tags):
            return ['np', ['adposition', 'to'] if tags['relation'] == 'recipient'
                    else ['adposition'], ['n', noun]]
        self._generate(noun, 'pronoun' if personal else 'noun', axes, tree,
                       'I' if personal else f'the {noun}', 'I' if personal else noun,
                       lambda t: personal or (t['definiteness'], t['number']) != ('adefinite', 'singular')
                       and (t['definiteness'], t['number']) != ('indefinite', 'plural'),
                       traversal=self.store(noun, points))

    def _verb(self, verb):
        self._generate(verb, 'verb', {'verb': verb, 'person': ['1', '2', '3'],
                       'number': ['singular', 'plural'], 'tense': ['present', 'past'],
                       'verb-form': 'finite', 'aspect': 'simple', 'mood': 'indicative'},
                       lambda t: ['v', verb], verb)

    def _adjective(self, adjective):
        self._generate(adjective, 'adjective', {'adjective': adjective,
                       'number': ['singular', 'plural'], 'gender': ['masculine', 'feminine', 'neuter'],
                       'case': ['nominative', 'oblique'], 'degree': ['positive', 'comparative', 'superlative']},
                       lambda t: ['adj', adjective], adjective)

    def selection(self, lexeme, text):
        return self.store(lexeme, self.lexemes[lexeme].bundle[text])

    def contractions(self, tokens):
        """Display overlays; source chips remain distinct and draggable.

        Each substitution is (tuple of pre-contraction tokens, contracted text).
        Return non-overlapping (start, stop, text) spans. English has none.
        """
        spans, i = [], 0
        while i < len(tokens):
            for source, target in self.substitutions:
                if tuple(tokens[i:i + len(source)]) == source:
                    spans.append((i, i + len(source), target))
                    i += len(source)
                    break
            else:
                i += 1
        return tuple(spans)
