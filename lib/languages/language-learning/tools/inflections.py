'''
"inflections.py" contains helpful datasets and 

See README.txt and GLOSSARY.txt for notes on terminology
'''

import collections
import re

from tools.transforms import (
    HtmlGroupPositioning, HtmlPersonPositioning,
    HtmlTextTransform,  HtmlNumberTransform, 
    HtmlTenseTransform, HtmlProgressTransform, HtmlNounFormTransform, HtmlBubble
)
from tools.shorthands import (
    Enclosures, BracketedShorthand, TextTransformShorthand,
    EmojiSubjectShorthand, EmojiAnnotationShorthand, EmojiPersonShorthand, EmojiNumberShorthand, 
    EmojiModifierShorthand, EmojiBubbleShorthand, EmojiPerson, EmojiInflectionShorthand
)

from tools.parsing import SeparatedValuesFileParsing, TermParsing, ListParsing
from tools.annotation import RowAnnotation, CellAnnotation
from tools.dictstores import DefaultDictLookup, DictLookup, DictSet
from tools.dictbundles import DictBundles
from tools.indexing import DictTupleIndexing, DictKeyIndexing
from tools.labels import TermLabelEditing, TermLabelFiltering
from tools.evaluation import KeyEvaluation, MultiKeyEvaluation
from tools.population import NestedLookupPopulation, FlatLookupPopulation, DictSetPopulation
from tools.nodemaps import ListTools, RuleTools
from tools.demonstration import TextDemonstration, EmojiDemonstration
from tools.cards import CardFormatting

dict_bundles = DictBundles()

case_episemaxis_to_episemes = {
    # NOTE: "role" is used in the sense of "semantic role", a.k.a. "thematic relation": https://en.wikipedia.org/wiki/Thematic_relation
    #   In our analysis, the "role" forms one part (an "episeme") of what is referred to here as "semantic case" (a "seme").
    #   The other part of semantic case is referred to as "motion", which is defined below.
    #   The term "semantic case" is used in a similar sense as "deep case" in existing literature.
    #   The term "semantic case" is introduced both to place distinction with "role" 
    #    and to create a paradigm where we map between language-agnostic "semantic" semes 
    #    and language-specific "grammatical" tags, e.g. "semantic mood" to "grammatical mood",  
    #    "semantic aspect" to "grammatical aspect", etc.
    #   Each language has a unique map from a semantic case to grammatical case, 
    #    and it is grammatical case that language learners are typically most familiar with (e.g. nominative, ablative, etc.)
    #   A language's map from semantic case to grammatical case is known as its "case usage".
    #   Semantic roles are also categorized into "macroroles" (i.e. subject, direct-object, indirect-object, adverbial) 
    #    and it is the macrorole that determines how noun phrases should be ordered within a clause.
    #   See README.txt and GLOSSARY.tsv for more information on these and related terms.
    'role': [
        # NON-INDIRECT:
        # 'existential', # a noun that is declared within an existential clause
        'agent',       # a sentient noun that is interacting with a "patient" or "theme"
        'force',       # a nonsentient noun that is interacting with a "patient" or "theme"
        'patient',     # a noun that passively undergoes a state change
        'theme',       # a noun that is passively mentioned without undergoing a state change
        'experiencer', # a noun that perceives a "stimulus"
        'stimulus',    # a noun that is being perceived by an "experiencer"
        'predicand',   # a noun that is considered part of a larger "predicate" set
        'predicate',   # a noun that is considered to contain a smaller "predicand" set
        # INDIRECT:
        'topic',       # a noun that is indicated as the topic of conversation, could be either indirect or nonindirect, and could exist in tandem with other nonindirect roles
        'comment',     # a noun that in some way relates to a "topic"
        'possessor',   # a noun that owns a "possession"
        'possession',  # a noun that is owned by a "possessor"
        'location', 'extent', 'vicinity', 'interior', 'medium', 'side', 'surface', 'subsurface', 
        'presence', 'aid', 'lack', 'interest', 'purpose', 
        'time', 'state-of-being', 'company', 'resemblance'],
    # NOTE: "motion" is introduced here as a grammatical episemaxis to capture certain kinds of motion based use cases
    #  that differ only in whether something is moving towards or away from them, whether something is staying still, or whether something is being leveraged
    # To illustrate, in Finnish motion is what distinguishes the "lative" case from the "allative" case.
    'subjectivity': 'addressee subject direct-object indirect-object adverbial adnominal verb'.split(),
    # the kind of relationship that the noun participates in
    'motion':  'departed associated acquired approached surpassed leveraged'.split(),
    # the kind of relationship that the noun participates in
    'valency': 'impersonal intransitive transitive'.split(),
    # whether the subject does the action voluntary, and if so, whether it was instigated
    'volition':         'proactive reactive voluntary involuntary'.split(),
}

mood_episemaxis_to_episemes = {
    # NOTE: "evidentiality", "logic", "confidence", etc. are small parts ("episemes") to a larger part (a "seme") of meaning known as the "semantic mood".
    # A "seme" is simply the domain of any map "seme→tag" that creates distinction 
    #  between the meaning that the speaker intends to convey and the grammatical decision that could be interpreted by the audience.
    # The names for semes are assigned here by appending "semantic" to the name of whatever tag they map to, i.e. "semantic case", "semantic mood", etc.
    # See README.txt and GLOSSARY.tsv for more information on these and related terms.
    # how the statement arises in the context of logical discourse
    'evidentiality': [
        'deliberated',    # addressee attests to the event, addressee determines if the event occurs, speaker is neutral
        'requested',      # addressee attests to the event, addressee determines if the event occurs, speaker offers no persuasion
        'encouraged',     # addressee attests to the event, addressee determines if the event occurs, speaker persuades by encouragement
        'implored',       # addressee attests to the event, addressee determines if the event occurs, speaker persuades by emphasis
        'pending',        # addressee attests to the event, addressee determines if the event occurs, no persuasion needed, addressee agrees and confirmation is pending
        'commanded',      # addressee attests to the event, addressee determines if the event occurs, no persuasion needed, addressee is subordinate
        'prayed',         # addressee attests to the event, addressee determines if the event occurs, no persuasion needed, addressee is supernatural
        'interrogated',   # addressee attests to the event, subject determines if the event occurs
        'promised',       # speaker attests to the event, speaker determines if the event occurs
        'presumed',       # speaker attests to the event, subject determines if the event occurs, actuality of event is considered, no evidence given
        'visual',         # speaker attests to the event, subject determines if the event occurs, actuality of event is considered, evidence is visual
        'nonvisual',      # speaker attests to the event, subject determines if the event occurs, actuality of event is considered, evidence is nonvisual
        'secondhand',     # speaker attests to the event, subject determines if the event occurs, actuality of event is considered, evidence is secondhand
        'thirdhand',      # speaker attests to the event, subject determines if the event occurs, actuality of event is considered, evidence is thirdhand
        'circumstantial', # speaker attests to the event, subject determines if the event occurs, actuality of event is considered, evidence is circumstantial in some way
        'means',          # speaker attests to the event, subject determines if the event occurs, actuality of event is considered, evidence is circumstantial, based on means
        'motive',         # speaker attests to the event, subject determines if the event occurs, actuality of event is considered, evidence is circumstantial, based on motive
        'necessity',      # speaker attests to the event, subject determines if the event occurs, actuality of event is considered, evidence is circumstantial, based on need
        'conceded',       # speaker attests to the event, subject determines if the event occurs, actuality of event is considered, evidence of addressee is recognized
        'proposed',       # speaker attests to the event, subject determines if the event occurs, actuality of event is considered, evidence provided elsewhere
        'supposed',       # speaker attests to the event, subject determines if the event occurs, actuality of event is not considered, evidence provided elsewhere
        'antecedent',     # speaker attests to the event, subject determines if the event occurs, actuality of event is not considered, evidence provided elsewhere
        'consequent',     # speaker attests to the event, subject determines if the event occurs, actuality of event is not considered, evidence is contingent on other event
        'wished',         # subject attests to the event, subject determines if the event occurs, speaker is invested in outcome
        'deferred',       # subject attests to the event, subject determines if the event occurs, speaker is not invested in outcome
    ],
    # whether the event is confirmed or denied
    'polarity':         'affirmative negative'.split(),
    # how likely the statement is to be true
    'confidence':       'confident probable possible'.split(),
    # how surprised the speaker depicts himself
    'surprise':         'surprised unsurprised'.split(),
    # how ironic the speaker is
    'irony':            'ironic unironic'.split(),
}

aspect_episemaxis_to_episemes = {
    # NOTE: "duration", "consistency", etc. form what is known as the "semantic aspect".
    # The "semantic aspect" is an instance of a broader concept that we refer to as "seme".
    # A "seme" is simply the domain of any map "seme→tag" that creates distinction 
    #  between the meaning that the speaker intends to convey and the set of meanings that could be interpreted by the audience.
    # The names for semes are assigned here by appending "semantic" to the name of whatever tag they map to, i.e. "semantic case", "semantic aspect", etc.
    # See README.txt and GLOSSARY.tsv for more information on these and related terms.
    # how long the event occurs for
    'duration':            'brief protracted indeterminate'.split(), 
    # how consistently the event occurs
    'progress':            'atomic atelic started unfinished attempted transitioning paused arrested resumed continued finished'.split(),
    # whether the event is one part in a sequence of events
    'consistency':         'momentary experiential habitual customary frequent incessant'.split(), 
    # whether the event has intermediate states, and if so, what state it is in
    'ordinality':          'nonordinal ordinal'.split(),
    # whether the event has affects that linger after its occurrence, and for how long
    'persistence':         'static impermanent persistant'.split(),
    # whether the event occurs in the recent past/future
    'recency':             'nonrecent recent arecent'.split(),
    # whether the event is associated with motion, and if so, what kind
    'trajectory':          'rectilinear reversing returning directionless motionless'.split(),
    # whether the event is distributed among entities, and if so, how
    'distribution':        'centralized decentralized undistributed'.split(),
}

tagaxis_to_tags = {

    # needed to lookup the argument that is used to demonstrate a verb
    'language-type':  'native foreign'.split(), 

    'plicity': 'implicit explicit'.split(),

    # 'encoding': 'attestation transliteration pronunciation'.split(),

    'script': 
        # scripts that were derived from the phoenecian alphabet:
        'latin cyrillic gothic greek hebrew arabic phoenician ipa transliteration '
        # scripts that borrow aesthetics from chinese logograms:
        'hirigana katakana hangul '
        # scripts that were derived from chinese logograms:
        'traditional-han simplified-han kanji hanja chữ-hán chữ-nôm '
        'devanagari bengali gujarati gurmukhi oria tibetan '
        'simhala malayalam tamil telugu kannada '
        'burmese khmer thai lao balinese javanese sudanese brahmic '
        # scripts that were derived from egyptian heiroglyphs:
        'coptic meroitic demotic hieratic '
        # broad categories of script to handle niche applications:
        'runes heiroglyphs cuneiform emoji'.split(),

    # needed for infinitives in Old English and Swedish
    'completion': 'full bare'.split(),

    # needed for Old English
    'strength':   'strong weak'.split(),

    # needed for finite forms
    'person':      '1 2 3 4'.split(),
    'number':      'singular dual trial paucal plural superplural'.split(),
    'definiteness':'definite indefinite adefinite'.split(),
    'clusivity':   'inclusive exclusive'.split(),

    # needed for Spanish
    'formality':  'familiar polite elevated informal formal tuteo voseo'.split(),

    'partitivity':'nonpartitive partitive bipartitive'.split(),
    'clitic':     'tonic prefix suffix proclitic mesoclitic endoclitic enclitic'.split(),
    'distance':   'proximal medial distal'.split(),

    # needed for possessive pronouns
    'possessor-person':    '1-possessor 2-possessor 3-possessor'.split(),
    'possessor-number':    'singular-possessor dual-possessor plural-possessor'.split(),
    'possessor-gender':    'masculine-possessor feminine-possessor neuter-possessor'.split(),
    'possessor-clusivity': 'inclusive-possessor exclusive-possessor'.split(),
    'possessor-formality': 'familiar-possessor polite-possessor elevated-possessor informal-possessor formal-possessor tuteo-possessor voseo-possessor'.split(),

    # needed for adjectives
    'degree':     'positive equative comparative superlative'.split(), # 

    # needed for gerunds, supines, participles, and gerundives
    'gender':     'masculine feminine gendered neuter'.split(), # language specific concept where something takes on grammatical forms associated with a sex, "gendered" is used instead of "common" to disambiguate it from the "common" noun-forms
    'virility':   'virile muliebrile avirile'.split(), # language specific where something takes on physical attributes associated with a sex
    'sex':        'male female sexless'.split(), # biological concept assigned at birth
    'animacy':    'animate inanimate'.split(), # language specific concept where something takes on grammatical forms associated with something that moves
    'humanity':   'human nonhuman'.split(), # member of homo sapiens
    'anthropomorphism': 'anthropomorphic nonanthropomorphic'.split(), # assumes a humanlike form
    'emphathizability': 'emphathizable unemphathizable'.split(), # ability to be emphathized with
    'rationality':'rational nonrational'.split(), #ability to apply structured thought
    'sapience':   'sapient nonsapient'.split(), #ability to think, regardless of whether it uses structured thought
    'sentience':  'sentient nonsentient'.split(), #ability to perceive things
    'motility':   'motile nonmotile'.split(),  # ability to perceptibly move of its own will
    'dynamism':   'dynamic nondynamic'.split(),  # ability to move (includes e.g. clouds, fire)
    'mobility':   'mobile immobile'.split(),  # ability to be moved
    'dominance':  'dominant nondominant'.split(),  # ability to command or use
    'servility':  'servile nonservile'.split(),  # ability to be commanded or used
    'danger':     'dangerous nondangerous'.split(),  # ability to cause harm
    'vitality':   'living nonliving'.split(),  # ability to grow and reproduce
    'physicality':'physical abstract'.split(), # ability to take physical form
    'case':       
        '''nominative ergative
           oblique accusative absolutive 
           genitive dative ablative locative instrumental vocative 
           prepositional abessive adessive allative comitative delative 
           elative essive essive-formal essive-modal exessive illative 
           inessive instructive instrumental-comitative sociative sublative superessive 
           temporal terminative translative disjunctive prepositional undeclined'''.split(),

    # how the valency of the verb is modified to emphasize or deemphasize certain participants
    'voice':      'active passive middle antipassive applicative causative'.split(),
    # when an event occurs relative to the present
    'tense':      'present past future'.split(), 
    # when an event occurs relative to a reference in time
    'relative-tense': 'before during after'.split(),

    'mood': 
        '''indicative subjunctive conditional 
           optative benedictive jussive probable 
           imperative prohibitive desiderative 
           dubitative hypothetical presumptive permissive 
           admirative ironic-admirative hortative eventitive 
           precative volitive involutive inferential 
           necessitative injunctive 
           suggestive comissive deliberative 
           propositive potential conative obligative'''.split(),

    'aspect': 
        '''simple perfective imperfective
           habitual continuous
           progressive nonprogressive
           stative terminative prospective consecutive usitative iterative
           momentaneous continuative durative repetitive conclusive
           semelfactive distributive diversative reversative transitional cursive
           completive prolongative seriative inchoative reversionary semeliterative segmentative'''.split(),

    # whether the event is confirmed or denied
    'polarity':         'affirmative negative'.split(),
    'recency':          'recent nonrecent arecent'.split(),

    # # needed for correlatives in general
    # 'abstraction': 'organization location origin destination time manner reason quality amount'.split(),

    # needed when creating demonstrations for declensions
    'template': 
        '''organization sapient 
           carnivore herbivore granivore fruitivore nectarivore detritivore seacreature 
           plant bodypart bodyfluid viscera 
           food item fixture liquid gas event location side surface interior 
           heat-source visible audible vice virtue size quality quantity manner reason concept'''.split(),

    # needed for quantifiers/correlatives
    'quantity':    'universal nonexistential assertive elective'.split(),

    # needed to distinguish pronouns from common nouns and to further distinguish types of pronouns
    'noun-form':  
        '''common personal 
           demonstrative interrogative quantifier numeral
           reciprocal relative reflexive emphatic-reflexive
           common-possessive personal-possessive reflexive-possessive'''.split(),

    # needed to distinguish forms of verb that require different kinds of lookups with different primary keys
    'verb-form':  'finite infinitive participle gerundive gerund adverbial supine group'.split(),
}

tag_to_tagaxis = dict_bundles.bundle_to_map(tagaxis_to_tags)
episemes_to_case_episemaxis = dict_bundles.bundle_to_map(case_episemaxis_to_episemes)
episemes_to_mood_episemaxis = dict_bundles.bundle_to_map(mood_episemaxis_to_episemes)
episemes_to_aspect_episemaxis = dict_bundles.bundle_to_map(aspect_episemaxis_to_episemes)

termaxis_to_terms = {
    **tagaxis_to_tags,
    **case_episemaxis_to_episemes,
    **mood_episemaxis_to_episemes,
    **aspect_episemaxis_to_episemes,
}

term_to_termaxis = dict_bundles.bundle_to_map(termaxis_to_terms)
parse_any = TermParsing(term_to_termaxis)

verbial_declension_hashing = parse_any.tokenindexing('verb voice number gender case script')

conjugation_template_lookups = DictLookup(
    'conjugation',
    DictKeyIndexing('verb-form'), 
    {
        # verbs that indicate a subject
        'finite': DictLookup(
            'finite',
            DictTupleIndexing([
                    'verb',           
                    'person',           
                    'number',           
                    'gender',     # needed for Russian
                    'formality',  # needed for Spanish ('voseo')
                    'polarity',   # needed for Spanish ('negative imperative')
                    'recency',    # needed for Italian ('nonrecent past')
                    'mood',        
                    'voice',           
                    'tense',           
                    'aspect',      
                    'script',     # needed for Greek, Russian, Sanskrit, etc.
                ])),
        # verbs that do not indicate a subject
        'infinitive': DictLookup(
            'infinitive',
            DictTupleIndexing([
                    'verb',           
                    'completion', # needed for Old English
                    'voice',      # needed for Latin, Swedish
                    'tense',      # needed for German, Latin
                    'aspect',     # needed for Greek
                    'script',     # needed for Emoji, Greek, Russian, Sanskrit, etc.
                ],
                {'completion':'bare'}
            )),
        # verbs used as adjectives, indicating that an action is done upon a noun at some point in time
        'participle': DictLookup(
            'participle',
            DictTupleIndexing([
                    'verb',           
                    'number',     # needed for German
                    'gender',     # needed for Latin, German, Russian
                    'case',       # needed for Latin, German
                    'voice',      # needed for Russian
                    'tense',      # needed for Greek, Russian, Spanish, Swedish, French
                    'aspect',     # needed for Greek, Latin, German, Russian
                    'script',
                ])),
        # verbs used as adverbs
        'adverbial': DictLookup(
            'adverbial',
            DictTupleIndexing([
                    'verb',           
                    'tense',      # needed for Russian
                    'script',
                ])),
        # verbs used as adjectives, indicating the purpose of something
        'gerundive': DictLookup('gerundive', verbial_declension_hashing),
        # verbs used as nouns
        'gerund': DictLookup('gerund', verbial_declension_hashing),
        # verbs used as nouns, indicating the objective of something
        'supine': DictLookup('supine', verbial_declension_hashing),
        # a pattern in conjugation that the verb is meant to demonstrate
        'group': DictLookup('group', DictKeyIndexing('verb')),
    })

basic_pronoun_declension_hashing = parse_any.termindexing('number gender animacy humanity partitivity case script')
reflexive_pronoun_declension_hashing = parse_any.termindexing('person number gender formality case script')

declension_template_lookups = DictLookup(
    'declension',
    DictKeyIndexing('noun-form'), 
    {
        'common': parse_any.tokenfield('common', 
            'noun number gender animacy definiteness partitivity degree strength case script', ''),
        'personal': parse_any.termfield('personal', 
            'person number gender clusivity formality case clitic script', ''),
        'common-possessive': parse_any.tokenfield('common-possessive', 
            'possessor-noun possessor-number number gender case clitic script', ''),
        'personal-possessive': parse_any.termfield('personal-possessive', 
            'possessor-person possessor-number possessor-gender possessor-clusivity possessor-formality number animacy gender case clitic script', ''),
        'reflexive-possessive': parse_any.termfield('reflexive-possessive', 
            'possessor-number number gender case clitic script', ''),
        'demonstrative': parse_any.termfield('demonstrative', 
            'distance number gender animacy partitivity case script', ''),
        'quantifier': parse_any.termfield('quantifier', 
            'quantity number gender animacy partitivity case script', ''),
        'interrogative':      DictLookup('interrogative',      basic_pronoun_declension_hashing),
        # 'indefinite':         DictLookup('indefinite',         basic_pronoun_declension_hashing),
        'relative':           DictLookup('relative',           basic_pronoun_declension_hashing),
        'numeral':            DictLookup('numeral',            basic_pronoun_declension_hashing),
        'reciprocal':         DictLookup('reciprocal',         reflexive_pronoun_declension_hashing),
        'reflexive':          DictLookup('reflexive',          reflexive_pronoun_declension_hashing),
        'emphatic-reflexive': DictLookup('emphatic-reflexive', reflexive_pronoun_declension_hashing),
    })

finite_annotation  = CellAnnotation(
    'inflection', tag_to_tagaxis, {}, {0:'verb'}, 
    {**tagaxis_to_tags, 'script':'latin', 'verb-form':'finite'})
nonfinite_annotation  = CellAnnotation(
    'inflection', tag_to_tagaxis, {}, {0:'verb'},
    {**tagaxis_to_tags, 'script':'latin', 'verb-form':'infinitive'})
personal_pronoun_annotation  = CellAnnotation(
    'inflection', tag_to_tagaxis, {}, {}, 
    {**tagaxis_to_tags, 'script':'latin', 'noun-form':'personal'})
pronoun_annotation  = CellAnnotation(
    'inflection', tag_to_tagaxis, {}, {}, 
    {**tagaxis_to_tags, 'script':'latin'})
possessive_pronoun_annotation  = CellAnnotation(
    'inflection', tag_to_tagaxis, {}, {},
    {**tagaxis_to_tags, 'script':'latin', 'noun-form':'personal-possessive'})
common_noun_annotation  = CellAnnotation(
    'inflection', tag_to_tagaxis, {}, {0:'noun'},
    {**tagaxis_to_tags, 'script':'latin', 'noun-form':'common', 'person':'3'})
emoji_noun_adjective_annotation  = CellAnnotation(
    'inflection', tag_to_tagaxis, {}, {0:'adjective',1:'noun'},
    {**tagaxis_to_tags, 'script':'latin', 'noun-form':'common', 'person':'3'})
emoji_noun_verb_annotation = RowAnnotation('flag noun verb emoji'.split())
emoji_verb_annotation = RowAnnotation('flag template verb emoji'.split())
emoji_noun_declensions_annotation = CellAnnotation(
    'inflection', term_to_termaxis, {}, {}, termaxis_to_terms)
mood_annotation = CellAnnotation(
    'inflection', {}, {0:'column'}, {0:'mood'}, {'script':'latin'})
declension_verb_annotation = CellAnnotation(
    'inflection', tag_to_tagaxis, {0:'language'}, {1:'verb'}, 
    {'script':'latin', 'verb-form':'finite','gender':['masculine','feminine','neuter']})
template_verb_annotation = CellAnnotation(
    'verb', term_to_termaxis, {0:'template'}, {}, {})
template_dummy_annotation = RowAnnotation('flag subjectivity verb voice valency dummy-motion dummy-role dummy-subjectivity dummy-definiteness dummy-noun'.split())
template_tree_annotation = RowAnnotation('flag valency subjectivity tree'.split())
noun_template_annotation = RowAnnotation('noun template'.split())

conjugation_population = NestedLookupPopulation(conjugation_template_lookups, KeyEvaluation('inflection'))
declension_population  = NestedLookupPopulation(declension_template_lookups, KeyEvaluation('inflection'))
emoji_noun_population = FlatLookupPopulation(DictLookup('emoji noun', DictTupleIndexing(['noun','number'])), KeyEvaluation('inflection'))
emoji_noun_adjective_population = FlatLookupPopulation(DictLookup('emoji noun adjective', DictTupleIndexing(['adjective','noun'])), KeyEvaluation('inflection'))
emoji_noun_verb_population = FlatLookupPopulation(DictLookup('emoji noun verb', DictTupleIndexing('noun verb'.split())), KeyEvaluation('emoji'))
emoji_verb_population = FlatLookupPopulation(DictLookup('emoji verb', DictTupleIndexing('template verb'.split())), KeyEvaluation('emoji'))
emoji_noun_declensions_population = FlatLookupPopulation(DictLookup('declension-templates', DictTupleIndexing('valency subjectivity motion role'.split())), KeyEvaluation('inflection'))
mood_population = FlatLookupPopulation(DictLookup('mood', DictTupleIndexing('mood column'.split())), KeyEvaluation('inflection'))
noun_template_population = DictSetPopulation(DictSet('noun-template', DictTupleIndexing('noun template'.split()), set()))
template_verb_population = DictSetPopulation(DictSet('template-verb', DictTupleIndexing('template role subjectivity valency verb'.split()), set()))
template_tree_population = FlatLookupPopulation(DictLookup('template-tree', DictTupleIndexing('valency subjectivity'.split())), KeyEvaluation('tree'))
template_dummy_population = FlatLookupPopulation(
    DictLookup('template-dummy', DictTupleIndexing('subjectivity verb voice valency'.split())), 
    MultiKeyEvaluation('dummy-motion dummy-role dummy-subjectivity dummy-definiteness dummy-noun'.split()) 
)

nonfinite_traversal = DictTupleIndexing(['tense', 'aspect', 'mood', 'voice'])

bracket_shorthand = BracketedShorthand(Enclosures())

html_group_positioning = HtmlGroupPositioning()

tsv_parsing = SeparatedValuesFileParsing()

template_verb_whitelist = (
    template_verb_population.index(
        template_verb_annotation.annotate(
            tsv_parsing.rows('data/inflection/template-verbs.tsv')))
)

template_dummy_lookup = (
    template_dummy_population.index(
        template_dummy_annotation.annotate(
            tsv_parsing.rows('data/inflection/template-dummies.tsv')))
)

noun_template_whitelist = (
    noun_template_population.index(
        noun_template_annotation.annotate(
            tsv_parsing.rows('data/inflection/noun-template.tsv')))
)

template_tree_lookup = (
    template_tree_population.index(
        template_tree_annotation.annotate(
            tsv_parsing.rows('data/inflection/template-trees.tsv')))
)

case_usage_dict = {
    **case_episemaxis_to_episemes,
    'script':tagaxis_to_tags['script'],
}
case_usage_annotation = CellAnnotation('case', 
    dict_bundles.bundle_to_map(case_usage_dict), {0:'column'}, {}, {})
case_usage_population = NestedLookupPopulation(
    DefaultDictLookup('case-usage', 
        DictTupleIndexing(
            'valency subjectivity motion role script'.split(),
            case_usage_dict,
        ),
        lambda dictkey: DictLookup('grammatical-case-columns',
            DictKeyIndexing('column'))),
    KeyEvaluation('case')
)

mood_usage_annotation = CellAnnotation('mood', dict_bundles.bundle_to_map(mood_episemaxis_to_episemes), {0:'column'}, {}, {}, debug=True)
mood_usage_population = NestedLookupPopulation(
    DefaultDictLookup('mood-usage', 
        DictTupleIndexing(
            [key for key in mood_episemaxis_to_episemes.keys()],
            mood_episemaxis_to_episemes,
        ),
        lambda dictkey: DictLookup('grammatical-mood-columns',
            DictKeyIndexing('column'))),
    KeyEvaluation('mood')
)

aspect_usage_annotation = CellAnnotation('aspect', dict_bundles.bundle_to_map(aspect_episemaxis_to_episemes), {0:'column'}, {}, {})
aspect_usage_population = NestedLookupPopulation(
    DefaultDictLookup('aspect-usage', 
        DictTupleIndexing(
            [key for key in aspect_episemaxis_to_episemes.keys()],
            aspect_episemaxis_to_episemes,
        ),
        lambda dictkey: DictLookup('grammatical-aspect-columns',
            DictKeyIndexing('column'))),
    KeyEvaluation('aspect'),
    # debug=True
)

nouns_to_depictions = {
    'animal':'cow',
    'thing':'bolt',
    'phenomenon': 'eruption',
};

LanguageSpecificTextDemonstration = TextDemonstration(
    TermLabelEditing(),
    TermLabelFiltering(),
    ListParsing(), 
    ListTools()
)

LanguageSpecificEmojiDemonstration = EmojiDemonstration(
    nouns_to_depictions,
    emoji_noun_adjective_population.index(
        emoji_noun_adjective_annotation.annotate(
            tsv_parsing.rows('data/inflection/emoji/noun-adjectives.tsv'))),
    emoji_noun_verb_population.index(
        emoji_noun_verb_annotation.annotate(
            tsv_parsing.rows('data/inflection/emoji/noun-verbs.tsv'))),
    emoji_noun_declensions_population.index(
        emoji_noun_declensions_annotation.annotate(
            tsv_parsing.rows('data/inflection/emoji/noun-declensions.tsv'))),
    emoji_noun_population.index(
        common_noun_annotation.annotate(
            tsv_parsing.rows('data/inflection/emoji/nouns.tsv'))),
    emoji_verb_population.index(
        emoji_verb_annotation.annotate(
            tsv_parsing.rows('data/inflection/emoji/verbs.tsv'))),
    mood_population.index(
        mood_annotation.annotate(
            tsv_parsing.rows('data/inflection/emoji/moods.tsv'))),
    TermLabelEditing(),
    TermLabelFiltering(),
    EmojiInflectionShorthand(
        EmojiSubjectShorthand(), 
        EmojiPersonShorthand(
            EmojiNumberShorthand(
                HtmlNumberTransform(
                    HtmlPersonPositioning(html_group_positioning)
                ), 
                bracket_shorthand
            )
        ),
        EmojiBubbleShorthand(HtmlBubble(), bracket_shorthand),
        TextTransformShorthand(HtmlTextTransform(), bracket_shorthand),
        EmojiAnnotationShorthand(html_group_positioning, bracket_shorthand),
        EmojiModifierShorthand(),
    ), 
    HtmlTenseTransform(), 
    HtmlProgressTransform(), 
    HtmlNounFormTransform(html_group_positioning)
)

def write(filename, rows):
    print(filename)
    with open(filename, 'w') as file:
        for row in rows:
            file.write(f'{row}\n')

def has_annotation(key, value):
    def _has_annotation(annotation):
        return key in annotation and annotation[key] == value or value in annotation[key]
    return _has_annotation

def replace(replacements):
    def _replace(content):
        for replaced, replacement in replacements:
            content = content.replace(replaced, replacement)
        return content
    return _replace

list_tools = ListTools()
rule_tools = RuleTools()
card_formatting = CardFormatting()

def mood_context(mood_templates):
    def mood_context_(tags, phrase):
        mood_prephrase = mood_templates[{**tags,'column':'prephrase'}]
        mood_postphrase = mood_templates[{**tags,'column':'postphrase'}]
        voice_prephrase = '[middle voice:]' if tags['voice'] == 'middle' else ''
        return ' '.join([voice_prephrase, mood_prephrase, phrase, mood_postphrase]).replace('∅','')
    return mood_context_

emoji_casts = {
    1: [
            EmojiPerson('s','n',1),
            EmojiPerson('s','f',2),
            EmojiPerson('s','m',3),
            EmojiPerson('s','n',4),
            EmojiPerson('s','n',5),
        ],
    2: [
            EmojiPerson('s','n',2),
            EmojiPerson('s','f',3),
            EmojiPerson('s','m',1),
            EmojiPerson('s','n',4),
            EmojiPerson('s','n',5),
        ],
    3: [
            EmojiPerson('s','n',3),
            EmojiPerson('s','f',4),
            EmojiPerson('s','m',2),
            EmojiPerson('s','n',1),
            EmojiPerson('s','n',5),
        ],
    4: [
            EmojiPerson('s','n',4),
            EmojiPerson('s','f',3),
            EmojiPerson('s','m',5),
            EmojiPerson('s','n',2),
            EmojiPerson('s','n',1),
        ],
    5: [
            EmojiPerson('s','n',5),
            EmojiPerson('s','f',4),
            EmojiPerson('s','m',3),
            EmojiPerson('s','n',2),
            EmojiPerson('s','n',1),
        ],
}

possessor_possession_whitelist = parse_any.tokenmask(
    'possessor_possession_whitelist', 
    'possessor-noun noun',
    '''
    man-possessor       brother
    man-possessor       sister
    man-possessor       attention
    man-possessor       boat
    man-possessor       book
    man-possessor       clothing
    man-possessor       dog
    man-possessor       food
    man-possessor       gift
    man-possessor       livestock
    man-possessor       horse
    man-possessor       house
    man-possessor       home
    man-possessor       love
    man-possessor       idea
    man-possessor       money
    man-possessor       name
    man-possessor       size
    man-possessor       shirt
    woman-possessor     brother
    woman-possessor     sister
    woman-possessor     attention
    woman-possessor     boat
    woman-possessor     book
    woman-possessor     clothing
    woman-possessor     dog
    woman-possessor     food
    woman-possessor     gift
    woman-possessor     livestock
    woman-possessor     horse
    woman-possessor     house
    woman-possessor     home
    woman-possessor     love
    woman-possessor     idea
    woman-possessor     money
    woman-possessor     name
    woman-possessor     size
    woman-possessor     shirt
    #dog-possessor      food # correct emoji is difficult to render
    dog-possessor       love
    dog-possessor       size
    dog-possessor       sound
    dog-possessor       name
    #animal-possessor   food # correct emoji is difficult to render
    animal-possessor    size
    animal-possessor    sound
    animal-possessor    name
    monster-possessor   home
    monster-possessor   food
    monster-possessor   size
    monster-possessor   sound
    monster-possessor   name
    snake-possessor     home
    snake-possessor     food
    snake-possessor     size
    snake-possessor     sound
    snake-possessor     name
    bug-possessor       food
    bug-possessor       idea
    bug-possessor       size
    bug-possessor       sound
    bug-possessor       name
    land-possessor      king
    land-possessor      queen
    land-possessor      size
    land-possessor      name
    house-possessor     size
    house-possessor     door
    house-possessor     window
''')


tag_defaults = parse_any.termaxis_to_term('''
    valency:      transitive
    subjectivity: direct-object
    
    clitic:       tonic
    clusivity:    exclusive
    formality:    informal
    definiteness: definite
    gender:       masculine
    animacy:      animate
    humanity:     human
    anthropomorphism: anthropomorphic
    emphathizability: emphathizable
    rationality:  rational
    sapience:     sapient
    sentience:    sentient
    motility:     motile
    dynamism:     dynamic
    mobility:     mobile
    dominance:    dominant
    servility:    servile
    danger:       nondangerous
    vitality:     living
    physicality:  physical
    #noun:        man
    noun-form:    common
    number:       singular
    partitivity:  nonpartitive
    person:       3
    strength:     strong

    degree:       positive

    duration:     brief
    progress:     atelic
    consistency:  momentary
    ordinality:   nonordinal
    persistence:  static
    recency:      arecent
    trajectory:   directionless
    distribution: undistributed

    evidentiality:presumed
    confidence:   confident
    polarity:     affirmative
    mood:         indicative

    tense:        present
    voice:        active
    completion:   bare

    verb-form:    finite
''')
