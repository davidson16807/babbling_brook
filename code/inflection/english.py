"""English for the dialog, written like the languages repo's `inflections_for_*.py` scripts.

Vocabulary, traversals, and masks are dictstores built with `TermParsing`; syntax trees
are `ListParsing` strings. Each word is rendered on its own, without the clause or phrase
around it: the tags of its traversal carry everything that context would. Demonstrations
are the repo's `LanguageSpecificTextDemonstration`, over an `Orthography` of a
`RuleLanguage` built from the repo's `english_language`, so every inflection is a `Rule`.

Nothing is generated when this module is imported. A lexeme is the term that distinguishes
it, a noun, verb, or adjective, or 'personal' for the personal pronouns. The dialog calls:
    inflections(lexeme)         the `Rule` of each tagpoint of the lexeme's traversal
    default_inflection(lexeme)  the `Rule` a newly placed word starts with
    inventory()                 lexeme → the `Rule`s its inventory entry shows, in inventory order
    lexeme(rule)                the lexeme a `Rule` of `inflections` inflects
    text(node)                  a `Rule`, a word, or None (a missing inflection), as the repo formats it
    clause()                    an empty 'clause' `Rule`, to which the player adds a statement's phrases

This module imports library modules: import it through `adapter.LanguagesLibrary.import_module`.
"""
from tools.dictbundles import DictBundles
from tools.dictstores import DictSpace, UniformDictLookup
from tools.indexing import DictTupleIndexing
from tools.inflections import (parse_any, tag_defaults, termaxis_to_terms,
                               LanguageSpecificTextDemonstration)
from tools.nodes import Rule
from tools.orthography import Orthography
from tools.parsing import TermParsing
from tools.treemaps import RuleTreeMap
from languages.english import english_language

from .InflectionGeneration import InflectionGeneration
from .RuleLanguage import RuleLanguage

termaxis_to_english_terms = {
    **termaxis_to_terms,
    **parse_any.token_to_tokens('''
        noun:      man ball boy dog house
        verb:      give talk walk
        adjective: big red
    '''),
}

parse = TermParsing(DictBundles().bundle_to_map(termaxis_to_english_terms))

constant = {
    term: DictSpace(term, DictTupleIndexing([termaxis]), {termaxis: term})
    for termaxis, terms in termaxis_to_english_terms.items() for term in terms
}

defaults = DictSpace('defaults', DictTupleIndexing([]), {**tag_defaults})

demonstration = LanguageSpecificTextDemonstration(
    Orthography('latin', RuleLanguage(
        english_language.semantics,
        english_language.grammar,
        english_language.tags,
        english_language.list_tools,
        english_language.substitutions,
    )),
    lambda tags, tree: tree,  # no context, such as the mood templates of flashcards
    lambda tree: tree,        # a `Rule`, not a card
)
noun_phrase = demonstration.generator(tree_lookup=UniformDictLookup('test np [adposition] [n noun]'))
verb_phrase = demonstration.generator(tree_lookup=UniformDictLookup('test vp [v verb]'))
adjective_phrase = demonstration.generator(tree_lookup=UniformDictLookup('test adj adjective'))

# Where a noun phrase sits in its clause; its adposition comes from case-usage.tsv.
placements = parse.termpath(
    'placements',
    'subjectivity motion role',
    '''
    subject        associated  agent
    direct-object  associated  patient
    adverbial      acquired    location   # to
    adverbial      departed    location   # away from
    adverbial      associated  interior   # in
    adverbial      associated  company    # with
    ''')

definitenesses_and_numbers = parse.termspace(
    'definitenesses_and_numbers',
    'definiteness number',
    '''
    definiteness: adefinite definite indefinite
    number:       singular plural
    ''')

pronouns = parse.termpath(
    'pronouns',
    'noun person number gender',
    '''
    man  1  singular  masculine
    man  2  singular  masculine
    man  3  singular  masculine
    man  3  singular  feminine
    man  3  singular  neuter
    man  1  plural    masculine
    man  2  plural    masculine
    man  3  plural    masculine
    ''')

subjects = parse.termpath(
    'subjects',
    'person number',
    '''
    1  singular
    2  singular
    3  singular
    1  plural
    2  plural
    3  plural
    ''')

tenses_and_progresses = parse.termspace(
    'tenses_and_progresses',
    'tense progress',
    '''
    tense:    present past future
    progress: atelic unfinished finished
    ''')

degrees = parse.termspace('degrees', 'degree', 'degree: positive comparative superlative')

# Agreement needs a case, which semantics derives from where its noun phrase sits.
adjective_placement = parse.termpath('adjective_placement', 'subjectivity motion role',
                                     'direct-object associated patient')

# The inflection a newly placed word starts with.
noun_default = parse.termmask('noun_default', 'definiteness number subjectivity', 'adefinite singular subject')
pronoun_default = parse.termmask('pronoun_default', 'person number subjectivity', '1 singular subject')
verb_default = parse.termmask('verb_default', 'person number tense progress', '1 singular present atelic')
adjective_default = parse.termmask('adjective_default', 'degree', 'positive')
pronoun_sample = parse.termmask('pronoun_sample', 'number subjectivity', 'singular subject')

# lexeme → (demonstration, default mask, traversal)
lexemes = {
    'personal': (noun_phrase, pronoun_default, pronouns * placements * constant['personal']),
    **{noun: (noun_phrase, noun_default,
              definitenesses_and_numbers * placements * constant['common'] * constant[noun])
       for noun in parse.terms('ball boy dog house')},
    **{verb: (verb_phrase, verb_default, tenses_and_progresses * subjects * constant[verb])
       for verb in parse.terms('give talk walk')},
    **{adjective: (adjective_phrase, adjective_default, degrees * adjective_placement * constant[adjective])
       for adjective in parse.terms('big red')},
}

generation = InflectionGeneration()

# How `Language.map` casts a `Rule` tree to a string, as its last step.
formatting = RuleTreeMap({tag: english_language.formatting.default for tag in RuleLanguage.RULES.split()})


def inflections(lexeme, mask=None):
    """The `Rule` of each tagpoint of the lexeme's traversal, or of those that `mask` contains.

    They are generated on each call. A mask that contains no tagpoint raises `ValueError`.
    """
    demonstration_, _, traversal = lexemes[lexeme]
    completed = defaults.override(traversal)
    if mask is not None:
        completed = completed & mask
    return [rule for _, [rule] in generation.generate([demonstration_], completed)]


def default_inflection(lexeme):
    """The `Rule` a newly placed word of the lexeme starts with, selected by its default mask."""
    _, default, _ = lexemes[lexeme]
    return inflections(lexeme, default)[0]


def inventory():
    """lexeme → the `Rule`s its inventory entry shows: the pronouns first, by a sample of three
    ("I, you, he"), then every other lexeme by its default inflection, by lexeme."""
    return {'personal': tuple(inflections('personal', pronoun_sample)[:3]),
            **{lexeme: (default_inflection(lexeme),) for lexeme in sorted(lexemes) if lexeme != 'personal'}}


def lexeme(rule):
    """The lexeme a `Rule` of `inflections` inflects, from the tags it was inflected with."""
    if rule.tag == 'np':
        return 'personal' if rule.tags['noun-form'] == 'personal' else rule.tags['noun']
    return rule.tags['verb'] if rule.tag == 'vp' else rule.tags['adjective']


def clause():
    """An empty 'clause' `Rule`: a statement before the player adds its phrases."""
    return Rule('clause', {}, [])


def text(node):
    """A `Rule`, a word, or None (a missing inflection), as the repo formats it: words that read
    as nothing ('∅') are left out, and None reads as '[MISSING]'."""
    return english_language.formatting.default(formatting, node)
