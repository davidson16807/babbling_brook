"""English for the dialog, written like the languages repo's `inflections_for_*.py` scripts.

Vocabulary, traversals, and masks are dictstores built with `TermParsing`; syntax
trees are `ListParsing` strings. Each word is rendered on its own, without the
clause or phrase around it: the tags of its traversal carry everything that context
would, so each tagpoint stored is exactly what was rendered. Demonstrations are the
repo's `LanguageSpecificTextDemonstration`, over an `Orthography` of a
`ListTreeLanguage` built from the repo's `english_language`.

For the dialog, this module computes, as the repo's scripts compute their decks:
    trees                lexeme → DictLookup of each tagpoint → the list tree it rendered as
    texts                lexeme → DictLookup of each tagpoint → the text its tree reads as
    fibers               lexeme → text → DictList of every tagpoint that reads as that text
    inflections          lexeme → text → the list tree of the first tagpoint in its fiber
    default_inflections  lexeme → the text a newly placed word starts with
    inventory            lexeme → the text the inventory shows, in inventory order
Each is composed from the one before with `ListTreeLookups`. Lexemes are the terms
that distinguish them: a noun, verb, or adjective, or 'personal' for the personal pronouns.

This module imports library modules: import it through
`adapter.LanguagesLibrary.import_module`.
"""
from tools.dictbundles import DictBundles
from tools.dictstores import DictLookup, DictSpace, UniformDictLookup
from tools.indexing import DictTupleIndexing
from tools.inflections import (parse_any, tag_defaults, termaxis_to_terms,
                               LanguageSpecificTextDemonstration)
from tools.orthography import Orthography
from tools.parsing import TermParsing
from languages.english import english_language

from .InflectionGeneration import InflectionGeneration
from .ListTreeLanguage import ListTreeLanguage
from .ListTreeLookups import ListTreeLookups
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
list_tree_lookups = ListTreeLookups(ListTrees(), dict_bundles)

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

def generated_trees(lexeme, demonstration, traversal):
    """Each tagpoint of the traversal → the list trees it renders as, one per demonstration."""
    completed = defaults.override(traversal)
    return DictLookup(lexeme, completed.indexing, {
        completed.indexing.tuplekey(tags): tree
        for tags, tree in inflection_generation.generate([demonstration], completed)})

def first(lookup, mask):
    """The value of `lookup` at the first of its tagpoints that `mask` contains."""
    restricted = list_tree_lookups.restrict(lookup, mask)
    if not restricted.content:
        raise ValueError(f'{mask.name} selects nothing in {lookup.name}')
    return next(iter(restricted.content.values()))

trees = {lexeme: generated_trees(lexeme, demonstration, traversal)
         for lexeme, (demonstration, _, traversal) in traversals.items()}
texts = {lexeme: list_tree_lookups.texts(lookup) for lexeme, lookup in trees.items()}
fibers = {lexeme: list_tree_lookups.fibers(lookup) for lexeme, lookup in texts.items()}
inflections = {lexeme: {text: trees[lexeme][tuplekey]
                        for text, tuplekey in list_tree_lookups.section(fibers[lexeme]).items()}
               for lexeme in trees}
default_inflections = {lexeme: first(texts[lexeme], default)
                       for lexeme, (_, default, _) in traversals.items()}

def listing(lexeme, mask, count=3):
    """The first texts with a tagpoint in `mask`, as in "I, you, he…"."""
    selected = list(dict.fromkeys(list_tree_lookups.restrict(texts[lexeme], mask).content.values()))
    return ', '.join(selected[:count]) + '…'

# Pronouns first, then alphabetical by what the inventory shows.
inventory = {'personal': listing('personal', pronoun_listing),
             **dict(sorted(((lexeme, text) for lexeme, text in default_inflections.items()
                            if lexeme != 'personal'), key=lambda item: item[1].casefold()))}
