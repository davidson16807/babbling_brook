"""Generate a game lexicon from the languages repo.

    git clone https://github.com/davidson16807/languages ../languages
    python tool/build_lexicon.py ../languages/language-learning data/lexicon/english.tsv

The languages repo is only used here. Building its English `Language` takes
about ten seconds, and its modules read data relative to the working
directory, so the game reads the generated table instead.

Every inflection is rendered by `Language.map` itself. A stand-in for the
language's `formatting` returns the ordered (part, text) tokens instead of a
joined string, which is what the dialog's chips need.
"""
import argparse
import copy
import itertools
import os
import re
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if 'babbling_brook' not in sys.modules:
    spec = spec_from_file_location('babbling_brook', ROOT / 'code' / '__init__.py',
                                   submodule_search_locations=[str(ROOT / 'code')])
    package = module_from_spec(spec)
    sys.modules['babbling_brook'] = package
    spec.loader.exec_module(package)

from babbling_brook.codec.LexiconCodec import LexiconStringCodec
from babbling_brook.model.Lexicon import Inflection, Lexeme, Lexicon, Token, tagpoint


# The mockup's vocabulary, plus "big" and "dog" to exercise adjective order and plurals.
# Avoid vowel-initial nouns until "a"/"an" is handled ("a apple").
ENGLISH_VOCABULARY = {
    'noun': ('ball', 'boy', 'dog', 'house'),
    'verb': ('give', 'talk', 'walk'),
    'adjective': ('big', 'red'),
}

# (subjectivity, motion, role) of each noun phrase the dialog offers.
ENGLISH_PLACEMENTS = (
    ('subject', 'associated', 'agent'),
    ('direct-object', 'associated', 'patient'),
    ('adverbial', 'acquired', 'location'),    # to
    ('adverbial', 'departed', 'location'),    # away from
    ('adverbial', 'associated', 'interior'),  # in
    ('adverbial', 'associated', 'company'),   # with
)

# English is built as the native gloss language of the flashcards, so it marks
# distinctions that English speakers don't make. A learner should see plain English.
ENGLISH_SUBSTITUTIONS = {'all you': 'you', 'all of you': 'you'}

PRONOUN_PERSONS = (
    ('1', 'singular', 'masculine'), ('2', 'singular', 'masculine'),
    ('3', 'singular', 'masculine'), ('3', 'singular', 'feminine'), ('3', 'singular', 'neuter'),
    ('1', 'plural', 'masculine'), ('2', 'plural', 'masculine'), ('3', 'plural', 'masculine'),
)


class TokenFormatting:
    """Takes the place of `RuleFormatting`: returns ordered tokens rather than text."""
    def __init__(self, Rule):
        self.Rule = Rule

    def default(self, treemap, element):
        tokens = []
        def walk(node, parent):
            if isinstance(node, self.Rule):
                for child in node.content:
                    walk(child, node)
            elif node is not None:
                tokens.append((parent.tag if parent is not None else '', node))
        walk(element, None)
        return tokens


class EnglishLexiconBuilder:
    def __init__(self, language, defaults):
        self.language = language
        self.defaults = defaults

    def tokens(self, tree, semes, parts):
        """Render `tree` and keep the tokens of the given parts, cleaned for display."""
        result = []
        for part, text in self.language.map(tree, 'latin', semes=semes):
            part = 'v' if part == 'vp' else part  # auxiliaries ("will") sit directly in the vp
            text = re.sub(r'\[[^\]]*\]|∅', '', str(text))
            text = re.sub(r'\s+', ' ', text).strip()
            text = ENGLISH_SUBSTITUTIONS.get(text, text)
            if part in parts and text:
                result.append(Token(part, text))
        return tuple(result)

    def lexeme(self, id, part, rows, display=None):
        """`rows` are (tags, tokens) in traversal order; the first is the default."""
        fibers = {}
        for tags, tokens in rows:
            if tokens:
                fibers.setdefault(tokens, []).append(tagpoint(tags))
        inflections = tuple(Inflection(tokens, tuple(points)) for tokens, points in fibers.items())
        default = inflections[0].text
        return Lexeme(id, part, display or default, default, inflections)

    def noun_tags(self, noun, definiteness, number, placement, noun_form='common', **extra):
        subjectivity, motion, role = placement
        return {'noun': noun, 'noun-form': noun_form, 'definiteness': definiteness,
                'number': number, 'subjectivity': subjectivity, 'motion': motion,
                'role': role, **extra}

    def noun_phrase(self, tags):
        tree = ['clause', ['phrase', ['np', ['adposition'], ['n', tags['noun']]]]]
        return self.tokens(tree, {'phrase': {**self.defaults, **tags}}, {'adposition', 'det', 'n'})

    def noun(self, noun):
        rows = []
        # Bare singular first, so the default matches what the inventory shows.
        for definiteness, number, placement in itertools.product(
                ('adefinite', 'definite', 'indefinite'), ('singular', 'plural'), ENGLISH_PLACEMENTS):
            tags = self.noun_tags(noun, definiteness, number, placement)
            rows.append((tags, self.noun_phrase(tags)))
        return self.lexeme(noun, 'noun', rows)

    def pronoun(self):
        rows = []
        for placement, (person, number, gender) in itertools.product(ENGLISH_PLACEMENTS, PRONOUN_PERSONS):
            tags = self.noun_tags('man', 'definite', number, placement, 'personal',
                                  person=person, gender=gender)
            rows.append((tags, self.noun_phrase(tags)))
        subjects = [tokens[0].text for tags, tokens in rows
                    if tags['subjectivity'] == 'subject' and tags['number'] == 'singular']
        return self.lexeme('pronoun', 'pronoun', rows, display=', '.join(subjects[:3]) + '…')

    def verb(self, verb):
        rows = []
        for tense, progress, (person, number, gender) in itertools.product(
                ('present', 'past', 'future'), ('atelic', 'unfinished', 'finished'),
                (persons for persons in PRONOUN_PERSONS if persons[2] == 'masculine')):
            tags = {'verb': verb, 'tense': tense, 'progress': progress,
                    'person': person, 'number': number}
            subject = {**self.defaults, **self.noun_tags('man', 'definite', number, ENGLISH_PLACEMENTS[0],
                                                          'personal', person=person, gender=gender),
                       **tags}
            tree = ['clause', ['subject', ['np', ['n', 'man']], ['vp', ['v', verb]]]]
            rows.append((tags, self.tokens(tree, {'subject': subject}, {'v'})))
        return self.lexeme(verb, 'verb', rows)

    def adjective(self, adjective):
        rows = []
        for degree in ('positive', 'comparative', 'superlative'):
            tags = {'adjective': adjective, 'degree': degree}
            phrase = {**self.defaults, **self.noun_tags('ball', 'definite', 'singular', ENGLISH_PLACEMENTS[1]),
                      'degree': degree}
            tree = ['clause', ['phrase', ['np', ['adj', adjective], ['n', 'ball']]]]
            rows.append((tags, self.tokens(tree, {'phrase': phrase}, {'adj'})))
        return self.lexeme(adjective, 'adjective', rows)

    def build(self, vocabulary):
        lexemes = [self.pronoun(),
                   *(self.noun(noun) for noun in vocabulary['noun']),
                   *(self.verb(verb) for verb in vocabulary['verb']),
                   *(self.adjective(adjective) for adjective in vocabulary['adjective'])]
        return Lexicon('english', {lexeme.id: lexeme for lexeme in lexemes})


def main(argv=None):
    parser = argparse.ArgumentParser(description='Generate a dialog lexicon from the languages repo')
    parser.add_argument('language_learning', type=Path,
                        help="The languages repo's language-learning directory")
    parser.add_argument('output', type=Path, help='Lexicon TSV to write')
    args = parser.parse_args(argv)
    output = args.output.resolve()
    # The languages repo imports `tools.*` and reads `data/...` relative to this directory.
    sys.path.insert(0, str(args.language_learning.resolve()))
    os.chdir(args.language_learning)
    from languages.english import english_language
    from tools.inflections import tag_defaults
    from tools.nodes import Rule
    language = copy.copy(english_language)
    language.formatting = TokenFormatting(Rule)
    lexicon = EnglishLexiconBuilder(language, dict(tag_defaults)).build(ENGLISH_VOCABULARY)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(LexiconStringCodec().encode(lexicon) + '\n', encoding='utf-8')
    for lexeme in lexicon.sorted():
        print(f'{lexeme.id:8} {lexeme.part:9} {len(lexeme.inflections):3} inflections, '
              f'{sum(len(i.tagpoints) for i in lexeme.inflections):3} tagpoints')


if __name__ == '__main__':
    main()
