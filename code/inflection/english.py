"""English for the dialog, written like the languages repo's `inflections_for_*.py` scripts.

Vocabulary, traversals, and masks are dictstores built with `TermParsing`; syntax
trees are `ListParsing` strings. Each word is rendered on its own, without the
clause or phrase around it: the tags of its traversal carry everything that context
would. Demonstrations are the
repo's `LanguageSpecificTextDemonstration`, over an `Orthography` of a
`ListTreeLanguage` built from the repo's `english_language`.

Nothing is generated when this module is imported. The dialog calls:
    inflections(lexeme)         the list tree of each tagpoint of the lexeme's traversal
    default_inflection(lexeme)  the list tree a newly placed word starts with
    inventory()                 lexeme → the text the inventory shows, in inventory order
Lexemes are the terms that distinguish them: a noun, verb, or adjective, or
'personal' for the personal pronouns.

This module imports library modules: import it through
`adapter.LanguagesLibrary.import_module`.
"""
from tools.dictbundles import DictBundles
from tools.dictstores import DictSpace, UniformDictLookup
from tools.indexing import DictTupleIndexing
from tools.inflections import (parse_any, tag_defaults, termaxis_to_terms,
                               LanguageSpecificTextDemonstration)
from tools.orthography import Orthography
from tools.parsing import TermParsing
from languages.english import english_language

from .InflectionGeneration import InflectionGeneration
from .ListTreeLanguage import ListTreeLanguage
from .ListTrees import ListTrees

english_termaxis_to_terms = {
    **termaxis_to_terms,
    **parse_any.token_to_tokens('''
        noun:      man ball boy dog house
        verb:      give talk walk
        adjective: big red
    '''),
}

dict_bundles = DictBundles()
list_trees = ListTrees()

english_term_to_termaxis = dict_bundles.bundle_to_map(english_termaxis_to_terms)

parse = TermParsing(english_term_to_termaxis)

constant = {
    term: DictSpace(term, DictTupleIndexing([termaxis]), {termaxis: term})
    for (term, termaxis) in english_term_to_termaxis.items()
}

defaults = DictSpace('defaults', DictTupleIndexing([]), {**tag_defaults})

nouns = parse.terms('ball boy dog house')
verbs = parse.terms('give talk walk')
adjectives = parse.terms('big red')

english_demonstration = LanguageSpecificTextDemonstration(
    Orthography('latin', ListTreeLanguage(
        english_language.semantics,
        english_language.grammar,
        english_language.tags,
        english_language.substitutions,
    )),
    lambda tags, tree: tree,  # no context, such as the mood templates of flashcards
    lambda tree: tree,        # a list tree, not a card
)

noun_phrase_demonstration = english_demonstration.generator(
    tree_lookup=UniformDictLookup('test np [adposition] [n noun]'))
verb_phrase_demonstration = english_demonstration.generator(
    tree_lookup=UniformDictLookup('test vp [v verb]'))
adjective_demonstration = english_demonstration.generator(
    tree_lookup=UniformDictLookup('test adj adjective'))

# Where a noun phrase sits in its clause; its adposition comes from case-usage.tsv.
placement_traversal = parse.termpath(
    'placement_traversal',
    'subjectivity motion role',
    '''
    subject        associated  agent
    direct-object  associated  patient
    adverbial      acquired    location   # to
    adverbial      departed    location   # away from
    adverbial      associated  interior   # in
    adverbial      associated  company    # with
    ''')

definiteness_number_space = parse.termspace(
    'definiteness_number_space',
    'definiteness number',
    '''
    definiteness: adefinite definite indefinite
    number:       singular plural
    ''')

pronoun_traversal = parse.termpath(
    'pronoun_traversal',
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

conjugation_subject_traversal = parse.termpath(
    'conjugation_subject_traversal',
    'person number',
    '''
    1  singular
    2  singular
    3  singular
    1  plural
    2  plural
    3  plural
    ''')

tense_progress_space = parse.termspace(
    'tense_progress_space',
    'tense progress',
    '''
    tense:    present past future
    progress: atelic unfinished finished
    ''')

degree_space = parse.termspace(
    'degree_space',
    'degree',
    'degree: positive comparative superlative')

# Agreement needs a case, which semantics derives from where the noun phrase sits.
adjective_placement_traversal = parse.termpath(
    'adjective_placement_traversal',
    'subjectivity motion role',
    'direct-object associated patient')

# The inflection a newly placed word starts with; the noun's matches the inventory.
noun_default = parse.termmask('noun_default', 'definiteness number subjectivity', 'adefinite singular subject')
pronoun_default = parse.termmask('pronoun_default', 'person number subjectivity', '1 singular subject')
verb_default = parse.termmask('verb_default', 'person number tense progress', '1 singular present atelic')
adjective_default = parse.termmask('adjective_default', 'degree', 'positive')
pronoun_listing = parse.termmask('pronoun_listing', 'number subjectivity', 'singular subject')

inflection_generation = InflectionGeneration()

traversals = {
    'personal': (noun_phrase_demonstration, pronoun_default,
                 pronoun_traversal * placement_traversal * constant['personal']),
    **{noun: (noun_phrase_demonstration, noun_default,
              definiteness_number_space * placement_traversal * constant['common'] * constant[noun])
       for noun in nouns},
    **{verb: (verb_phrase_demonstration, verb_default,
              tense_progress_space * conjugation_subject_traversal * constant[verb])
       for verb in verbs},
    **{adjective: (adjective_demonstration, adjective_default,
                   degree_space * adjective_placement_traversal * constant[adjective])
       for adjective in adjectives},
}

def inflections(lexeme, mask=None):
    """The list tree of each tagpoint of `lexeme`'s traversal, or of those that `mask` contains.

    They are generated on each call. A mask that contains no tagpoint raises `ValueError`.
    """
    demonstration, _, traversal = traversals[lexeme]
    completed = defaults.override(traversal)
    if mask is not None:
        completed = completed & mask
    return [tree for _, [tree] in inflection_generation.generate([demonstration], completed)]

def default_inflection(lexeme):
    """The list tree a newly placed word of `lexeme` starts with, selected by its default mask."""
    _, default, _ = traversals[lexeme]
    return inflections(lexeme, default)[0]

def inventory():
    """lexeme → the text the inventory shows: the pronouns, as in "I, you, he…", then the rest
    alphabetically by their default inflection."""
    pronouns = list(dict.fromkeys(list_trees.text(tree) for tree in inflections('personal', pronoun_listing)))
    others = {lexeme: list_trees.text(default_inflection(lexeme)) for lexeme in traversals if lexeme != 'personal'}
    return {'personal': ', '.join(pronouns[:3]) + '…',
            **dict(sorted(others.items(), key=lambda item: item[1].casefold()))}
