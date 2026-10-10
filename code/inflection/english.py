"""English for the dialog, written like the languages repo's `inflections_for_*.py` scripts.

Vocabulary, traversals, and masks are dictstores built with `TermParsing`; syntax
trees are `ListParsing` strings. Each word is rendered on its own, without the
clause or phrase around it: the tags of its traversal and of its `tag_templates`
carry everything that context would. Demonstrations are the repo's
`LanguageSpecificTextDemonstration`, over an `Orthography` of a `ListTreeLanguage`
built from the repo's `english_language`.

This module imports library modules: import it through
`adapter.LanguagesLibrary.import_module`.
"""
from tools.dictstores import DictSpace, UniformDictLookup
from tools.indexing import DictTupleIndexing
from tools.inflections import (dict_bundle_to_map, parse_any, tag_defaults, termaxis_to_terms,
                               LanguageSpecificTextDemonstration)
from tools.orthography import Orthography
from tools.parsing import TermParsing
from languages.english import english_language

from ..model.Lexicon import Lexicon
from .InflectionGeneration import InflectionGeneration
from .ListTreeLanguage import ListTreeLanguage, list_tree_tokens
from .bundles import lexeme

english_termaxis_to_terms = {
    **termaxis_to_terms,
    **parse_any.token_to_tokens('''
        noun:      man ball boy dog house
        verb:      give talk walk
        adjective: big red
    '''),
}

english_term_to_termaxis = dict_bundle_to_map(english_termaxis_to_terms)

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
    list_tree_tokens,
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

noun_templates = {'test': parse.termaxis_to_term('common')}
pronoun_templates = {'test': parse.termaxis_to_term('personal')}
verb_templates = {}
# Agreement needs a case, which semantics derives from where the noun phrase sits.
adjective_templates = {'test': parse.termaxis_to_term('direct-object associated patient')}

# The inflection a newly placed word starts with; the noun's matches the inventory.
noun_default = parse.termmask('noun_default', 'definiteness number subjectivity', 'adefinite singular subject')
pronoun_default = parse.termmask('pronoun_default', 'person number subjectivity', '1 singular subject')
verb_default = parse.termmask('verb_default', 'person number tense progress', '1 singular present atelic')
adjective_default = parse.termmask('adjective_default', 'degree', 'positive')
pronoun_listing = parse.termmask('pronoun_listing', 'number subjectivity', 'singular subject')

inflection_generation = InflectionGeneration()


def english_lexicon():
    generate = inflection_generation.generate
    lexemes = [
        lexeme('pronoun', 'pronoun',
               generate([noun_phrase_demonstration],
                        defaults.override(pronoun_traversal * placement_traversal),
                        pronoun_templates),
               pronoun_default, pronoun_listing),
        *(lexeme(noun, 'noun',
                 generate([noun_phrase_demonstration],
                          defaults.override(definiteness_number_space * placement_traversal * constant[noun]),
                          noun_templates),
                 noun_default)
          for noun in nouns),
        *(lexeme(verb, 'verb',
                 generate([verb_phrase_demonstration],
                          defaults.override(tense_progress_space * conjugation_subject_traversal * constant[verb]),
                          verb_templates),
                 verb_default)
          for verb in verbs),
        *(lexeme(adjective, 'adjective',
                 generate([adjective_demonstration],
                          defaults.override(degree_space * constant[adjective]),
                          adjective_templates),
                 adjective_default)
          for adjective in adjectives),
    ]
    return Lexicon('english', {lexeme.id: lexeme for lexeme in lexemes})
