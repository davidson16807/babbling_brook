"""English for the dialog, written like the languages repo's `inflections_for_*.py` scripts.

Vocabulary, traversals, and masks are dictstores built with `TermParsing`; syntax
trees are `ListParsing` strings like those of `data/inflection/template-trees.tsv`.
Each part of speech renders every tagpoint of its traversal with the repo's own
`english_language`, so adding a word or a tag here is the whole change.

This module imports library modules: import it through
`adapter.LanguagesLibrary.import_module`.
"""
from tools.dictstores import DictSpace
from tools.indexing import DictTupleIndexing
from tools.inflections import dict_bundle_to_map, parse_any, tag_defaults, termaxis_to_terms
from tools.parsing import TermParsing
from languages.english import english_language

from .LexiconGeneration import LexiconGeneration, PartOfSpeech

english_termaxis_to_terms = {
    **termaxis_to_terms,
    **parse_any.token_to_tokens('''
        noun:      man ball boy dog house
        verb:      give talk walk
        adjective: big red
    '''),
}

parse = TermParsing(dict_bundle_to_map(english_termaxis_to_terms))

defaults = DictSpace('defaults', DictTupleIndexing([]), {**tag_defaults})

# Where a noun phrase sits in its clause; the adpositions come from case-usage.tsv.
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

noun_space = parse.termspace(
    'noun_space',
    'noun',
    'noun: ball boy dog house')

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

verb_space = parse.termspace(
    'verb_space',
    'verb',
    'verb: give talk walk')

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

adjective_space = parse.termspace(
    'adjective_space',
    'adjective',
    'adjective: big red')

degree_space = parse.termspace(
    'degree_space',
    'degree',
    'degree: positive comparative superlative')

noun = PartOfSpeech(
    'noun',
    'clause [test np [adposition] [n noun]]',
    parse.termaxis_to_term('common'),
    frozenset({'adposition', 'det', 'n'}),
    # Bare and singular, so the default matches what the inventory shows.
    parse.termmask('noun_default', 'definiteness number subjectivity', 'adefinite singular subject'),
)

pronoun = PartOfSpeech(
    'pronoun',
    'clause [test np [adposition] [n noun]]',
    parse.termaxis_to_term('personal definite'),
    frozenset({'adposition', 'n'}),
    parse.termmask('pronoun_default', 'person number subjectivity', '1 singular subject'),
)

verb = PartOfSpeech(
    'verb',
    'clause [test [np [n noun]] [vp v verb]]',
    # The subject is a pronoun, so that person and number reach the verb.
    parse.termaxis_to_term('man personal subject associated agent'),
    frozenset({'v', 'vp'}),
    parse.termmask('verb_default', 'person number tense progress', '1 singular present atelic'),
)

adjective = PartOfSpeech(
    'adjective',
    'clause [test np [adj adjective] [n noun]]',
    parse.termaxis_to_term('ball common definite singular direct-object associated patient'),
    frozenset({'adj'}),
    parse.termmask('adjective_default', 'degree', 'positive'),
)

pronoun_listing = parse.termmask('pronoun_listing', 'number subjectivity', 'singular subject')


def english_lexicon():
    generation = LexiconGeneration(english_language, defaults)
    return generation.lexicon('english', [
        generation.lexeme(pronoun, pronoun_traversal * placement_traversal, 'pronoun', pronoun_listing),
        *generation.lexemes(noun, definiteness_number_space * placement_traversal * noun_space, 'noun'),
        *generation.lexemes(verb, tense_progress_space * conjugation_subject_traversal * verb_space, 'verb'),
        *generation.lexemes(adjective, degree_space * adjective_space, 'adjective'),
    ])
