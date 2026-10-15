# HUMAN VETTED

"""English for the dialog, written like the languages repo's `inflections_for_*.py` scripts.

Nothing is generated when this module is imported. The dialog calls (TODO: we should really move this to a class category):
    inflections(lexeme)         a `DialogRule` tree per way the lexeme's inflections read
    default_inflection(lexeme)  the `DialogRule` tree a newly placed word starts with
    inventory()                 lexeme → the `DialogRule` trees its inventory entry shows, in inventory order
    lexeme(rule)                the lexeme a `DialogRule` tree of `inflections` inflects
    clause()                    an empty 'clause' `DialogRule`, to which the player adds the statement's phrases
    text(node)                  what a `DialogRule` tree, or a word in one, reads as
    you()                       the 2nd person singular pronoun, which marks what the player says
    speak()                     the 2nd person singular imperative of "speak", which labels the button that speaks

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

from .DialogRule import DialogRule
from .DialogRuleFormatting import DialogRuleFormatting
from .InflectionGeneration import InflectionGeneration
from .DialogRules import DialogRules
from .DialogLanguage import DialogLanguage

english_termaxis_to_terms = {
    **termaxis_to_terms,
    **parse_any.token_to_tokens('''
        noun:      man ball boy dog house
        verb:      give talk walk speak
        adjective: big red
    '''),
}

dict_bundles = DictBundles()

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
    Orthography('latin', DialogLanguage(
        english_language.semantics,
        english_language.grammar,
        english_language.tags,
        english_language.list_tools,
        english_language.substitutions,
    )),
    lambda tags, tree: tree,  # no context, such as the mood templates of flashcards
    lambda tree: tree,        # a `Rule` tree, not a card
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

number_space = parse.termspace(
    'number_space',
    'number',
    'number: singular plural')

# An adjective is generated for every place and number of the noun phrase it may modify, so
# that it can be checked to agree with that noun phrase. In English these read alike, and
# share a cell of the grid.
adjective_agreement_traversal = placement_traversal * number_space

# The inflection a newly placed word starts with; the noun's matches the inventory.
noun_default = parse.termmask('noun_default', 'definiteness number subjectivity', 'adefinite singular subject')
pronoun_default = parse.termmask('pronoun_default', 'person number subjectivity', '1 singular subject')
verb_default = parse.termmask('verb_default', 'person number tense progress', '1 singular present atelic')
adjective_default = parse.termmask('adjective_default', 'degree', 'positive')
# "speak" labels the button that speaks; it is not in the inventory.
speak_traversal = parse.termpath(
    'speak_traversal',
    'verb mood person number tense',
    'speak imperative 2 singular present')

you_mask = parse.termmask('you_mask', 'person number subjectivity', '2 singular subject')
pronoun_listing = parse.termmask('pronoun_listing', 'number subjectivity', 'singular subject')

# Tagaxes on which a verb agrees with its subject, and a modifier, such as an adjective, with
# the noun phrase it modifies; see DialogRuleMeaning.py.
subject_agreement = ('person', 'number')
modifier_agreement = ('number', 'gender', 'case')

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
                   degree_space * adjective_agreement_traversal * constant[adjective])
       for adjective in adjectives},
}

def inflections(lexeme, mask=None):
    """A `DialogRule` tree per way the tagpoints of `lexeme`'s traversal read, or those that
    `mask` contains. Each node lists, as `tags`, its tags in every tagpoint that reads so (see
    DialogRules.py). They are generated on each call. A mask that contains no tagpoint raises
    `ValueError`.
    """
    demonstration, _, traversal = traversals[lexeme]
    completed = defaults.override(traversal)
    if mask is not None:
        completed = completed & mask
    return homonyms.group(tree for _, [tree] in inflection_generation.generate([demonstration], completed))

def default_inflection(lexeme):
    """The `DialogRule` tree a newly placed word of `lexeme` starts with, selected by its default mask.

    It lists only the default's tags, not those of its homonyms: `inflections(lexeme)` has the
    `DialogRule` tree that reads the same and lists them all."""
    _, default, _ = traversals[lexeme]
    return inflections(lexeme, default)[0]

def inventory():
    """lexeme → the `DialogRule` trees its inventory entry shows: the pronouns first, by their first
    three singular subjects ("I, you, he"), then every other lexeme by its default inflection."""
    return {'personal': tuple(inflections('personal', pronoun_listing)[:3]),
            **{lexeme: (default_inflection(lexeme),) for lexeme in sorted(traversals) if lexeme != 'personal'}}

def lexeme(rule):
    """The lexeme a `DialogRule` tree of `inflections` inflects, from the tags it was inflected
    with. Its homonyms are inflections of one lexeme, so the first homonym's tags will do."""
    tags = rule.tags[0]
    if rule.tag == 'np':
        return 'personal' if tags['noun-form'] == 'personal' else tags['noun']
    return tags['verb'] if rule.tag == 'vp' else tags['adjective']

def you():
    """The 2nd person singular pronoun, as a subject: it marks what the player says, as in "you: …"."""
    return inflections('personal', you_mask)[0]

def speak():
    """The 2nd person singular imperative of "speak", which labels the button that speaks."""
    completed = defaults.override(speak_traversal)
    return homonyms.group(tree for _, [tree] in inflection_generation.generate([verb_phrase_demonstration], completed))[0]

def clause():
    """An empty 'clause' `DialogRule`: a statement before the player adds its phrases.
    It is not inflected, so it has one reading, with no tags."""
    return DialogRule('clause', [{}], [])

formatting = DialogRuleFormatting()

def text(node):
    """What a `DialogRule` tree, or a word in one, reads as."""
    return formatting.format(node)

homonyms = DialogRules(formatting)
