import re

from tools.evaluation import KeyEvaluation
from tools.population import NestedLookupPopulation
from tools.languages import Language
from tools.orthography import Orthography
from tools.nodes import Rule
from tools.nodemaps import (
    ListTools, ListGrammar, ListSemantics,
    RuleTools, RuleSyntax, RuleFormatting, 
)
from tools.dictstores import DictLookup, NestedDictLookup, FallbackDictLookup, ProceduralLookup
from tools.indexing import DictKeyIndexing
from tools.cards import CardFormatting
from tools.inflections import (
    case_usage_population, mood_usage_population, aspect_usage_population, 
    declension_population, mood_population,
    case_usage_annotation, mood_usage_annotation, aspect_usage_annotation, 
    pronoun_annotation, common_noun_annotation, possessive_pronoun_annotation, 
    finite_annotation, mood_annotation,
    tsv_parsing,
    parse_any,
    LanguageSpecificTextDemonstration
)


class RegularEnglishGrammar:
    def __init__(self):
        self.plural_regex = [
            (r"(?i)(ous)$", r'ous'),
            (r"(?i)(man)$", r'men'),
            (r"(?i)(quiz)$", r'\1zes'),
            (r"(?i)^(oxen)$", r'\1'),
            (r"(?i)^(ox)$", r'\1en'),
            (r"(?i)(m|l)ice$", r'\1ice'),
            (r"(?i)(m|l)ouse$", r'\1ice'),
            (r"(?i)(passer)s?by$", r'\1sby'),
            (r"(?i)(matr|vert|ind)(?:ix|ex)$", r'\1ices'),
            (r"(?i)(x|ch|ss|sh)$", r'\1es'),
            (r"(?i)([^aeiouy]|qu)y$", r'\1ies'),
            (r"(?i)(hive)$", r'\1s'),
            (r"(?i)([lr])f$", r'\1ves'),
            (r"(?i)(staff)$", r'staves'),
            (r"(?i)([^f])fe$", r'\1ves'),
            (r"(?i)sis$", 'ses'),
            (r"(?i)([ti])a$", r'\1a'),
            (r"(?i)([ti])um$", r'\1a'),
            (r"(?i)(buffal|potat|tomat)o$", r'\1oes'),
            (r"(?i)(bu)s$", r'\1ses'),
            (r"(?i)(alias|status)$", r'\1es'),
            (r"(?i)(octop|vir)i$", r'\1i'),
            (r"(?i)(octop|vir)us$", r'\1i'),
            (r"(?i)^(ax|test)is$", r'\1es'),
            (r"(?i)s$", r's'),
            (r"$", r's'),
        ]
        self.uncountables = set('''
            equipment jeans money rice series sheep 
            species information livestock English'''.split())
        self.irregular_plurals =[
            ('staff', 'staves'),
            ('tooth', 'teeth'),
            ('person', 'people'),
            ('human', 'humans'),
            ('child', 'children'),
            ('move', 'moves'),
            ('zombie', 'zombies'),
            ('sex', 'sexes'),
            ('phenomenon', 'phenomena'),
            ('datum', 'data'),
            ('goose', 'geese'),
        ]
        self.singular_third_regex = [
            (r"(?i)([^aeiouy])y$", r'\1ies'),
            (r"(?i)([zs])$", r'\1es'),
            (r"$", r's'),
        ]
        self.perfective_regex = [
            (r"(?i)ay$", r'aid'),
            (r"(?i)([^aeiou])y$", r'\1ied'),
            (r"(?i)([^aeiouyw])$", r'\1ed'),
            (r"$", r'd'),
        ]
        self.imperfective_regex = [
            (r"(?i)e$", r'ing'),
            (r"$", r'ing'),
        ]
    def plural_noun(self, noun):
        if noun in self.uncountables:
            return noun
        if noun in self.irregular_plurals:
            return self.irregular_plurals[noun]
        for replaced, replacement in self.plural_regex:
            if re.search(replaced, noun):
                return re.sub(replaced, replacement, noun)
    def singular_third_verb(self, verb):
        for replaced, replacement in self.singular_third_regex:
            if re.search(replaced, verb):
                return re.sub(replaced, replacement, verb)
    def perfective_verb(self, verb):
        for replaced, replacement in self.perfective_regex:
            if re.search(replaced, verb):
                return re.sub(replaced, replacement, verb)
    def imperfective_verb(self, verb):
        for replaced, replacement in self.imperfective_regex:
            if re.search(replaced, verb):
                return re.sub(replaced, replacement, verb)
    def decline(self, tags):
        is_plural = tags['number']!='singular'
        is_possessive = tags['case']=='possessive'
        noun = tags['noun']
        noun = noun if not is_plural else self.plural_noun(noun)
        noun = noun if not is_possessive else noun+"'" if noun.endswith("s") and is_plural else noun+"'s"
        return noun
    def conjugate(self, tags):
        verb = tags['verb']
        if tags['aspect']=='imperfective':
            return self.imperfective_verb(verb)
        if tags['tense']=='past' or tags['aspect']=='perfective':
            return self.perfective_verb(verb)
        if tags['number']=='singular' and tags['person']=='3' and tags['verb-form']=='finite':
            return self.singular_third_verb(verb)
        return verb
    def agree(self, tags):
        return tags['noun']#lol

class EnglishListSubstitution:
    def __init__(self):
        pass
    def verbform(self, machine, tree, memory):
        '''same as self.inflection.conjugate(), but creates auxillary verb phrases when conjugation of a single verb is insufficient'''
        form = memory['verb-form']
        tense = memory['tense']
        voice = memory['voice']
        if form  == 'participle': 
            return [['adposition','that'], 'finite', tree]
        return tree
    def mood(self, machine, tree, memory):
        '''creates auxillary verb phrases when necessary to express mood'''
        mood = memory['mood']
        lookup = {
            'conditional':  ['indicative', 'would', 'infinitive', tree],
            'jussive':      ['indicative', 'should', 'infinitive', tree],
            'eventitive':   ['indicative', 'likely', 'infinitive', tree],
            'hypothetical': ['indicative', 'might', 'infinitive', tree],
            'desiderative': ['indicative', ['v','want'], 'to', 'infinitive', tree],
            'necessitative':['indicative', ['v','need'], 'to', 'infinitive', tree],
            'potential':    ['indicative', ['v','be able'], 'to', 'infinitive', tree],
            # NOTE: the following are nice ideas, but can be misinterpreted as supposition, 
            # and are superfluous if other markers are added to disambiguate:
            # 'imperative':   ['indicative', 'must', 'infinitive', tree],
            # 'prohibitive':  ['indicative', 'must', 'not', 'infinitive', tree],
        }
        return tree if mood not in lookup else lookup[mood]
    def tense(self, machine, tree, memory):
        '''creates auxillary verb phrases and bracketed subtext when necessary to express tense'''
        tense = memory['tense']
        verbform = memory['verb-form']
        if (tense, verbform) == ('future', 'finite'):       return ['will',        'infinitive', tree]
        # if (tense, verbform) == ('future', 'infinitive'):   return ['will',        'infinitive', tree]
        if (tense, verbform) == ('past',   'infinitive'):   return ['[back then]', tree]
        # if (tense, verbform) == ('present','infinitive'):   return ['[right now]', tree]
        if (tense, verbform) == ('future', 'infinitive'):   return ['[later on]',   tree]
        return tree
    def aspect(self, machine, tree, memory):
        '''creates auxillary verb phrases when necessary to express aspect'''
        tense = memory['tense']
        duration = memory['duration']
        progress = memory['progress']
        consistency = memory['consistency']
        ordinality = memory['ordinality']
        persistence = memory['persistence']
        recency = memory['recency']
        trajectory = memory['trajectory']
        distribution = memory['distribution']
        preverb = []
        postverb = []
        if duration == 'protracted':
            postverb.append('[on and on]')
        if duration == 'indeterminate':
            postverb.append('[on and on endlessly]')
        if progress == 'unfinished':
            postverb.append('[still unfinished]')
        if ordinality == 'ordinal':
            postverb.append('[as part of a larger event]')
        if persistence == 'impermanent':
            postverb.append('[that changed things a while after]')
        if persistence == 'persistant':
            postverb.append('[that changed things]')
        postverb.append({
            ('recent',    'past'):    '[just recently]',
            ('recent',    'present'): '[just now]',
            ('recent',    'future'):  '[not long from now]',
            ('nonrecent', 'past'):    '[long ago]',
            ('nonrecent', 'present'): '',
            ('nonrecent', 'future'):  '[long from now]',
            ('arecent',   'past'):    '',
            ('arecent',   'present'): '',
            ('arecent',   'future'):  '',
        }[recency, tense])
        postverb.append({
            'rectilinear':    '[in a straight line]',
            'reversing':      '[reversing previous direction]',
            'returning':      '[returning to the start]',
            'motionless':     '[motionless]',
            'directionless':  '',
        }[trajectory])
        postverb.append({
            'centralized':     '[together]',
            'decentralized':   '[coming apart]',
            'undistributed':   '',
        }[distribution])
        preverb.append({
            'incessant': '[incessantly]',
            'habitual':  '[habitually]',
            'customary': '[customarily]',
            'frequent':  '[frequently]',
            'experiential':'',
            'momentary':  '',
        }[consistency])
        if progress in {'paused', 'resumed', 'continued', 'arrested'}:
            aspect = progress
        elif consistency in {'experiential'}:
            aspect = consistency
        elif any([
                persistence in {'impermanent','persistant'},
                recency in {'recent'},
                progress in {'atomic', 'finished'},
                consistency in {'experiential'}]):
            aspect = 'perfective'
        elif progress in {'started', 'unfinished'}:
            if duration in {'brief'}:
                aspect = 'imperfective'
            else:
                aspect = 'perfective-progressive'
        else:
            aspect = 'simple'
        aspect_to_tree = {
            'arrested':               [['passive','simple', 'implicit', 'v', 'halt'], 'from', 'finite', ['unfinished', tree]],
            'paused':                 [['active', 'simple', 'implicit', 'v', 'pause'], 'finite', ['unfinished', tree]],
            'resumed':                [['active', 'simple', 'implicit', 'v', 'resume'], 'finite', ['unfinished', tree]],
            'continued':              [['active', 'simple', 'implicit', 'v', 'continue'], 'finite', ['unfinished', tree]],
            # 'finished':             [['active', 'simple', 'implicit', 'v', 'finish'], 'finite', ['unfinished', tree]],
            'experiential':           [['active', 'simple', 'implicit', 'v', 'experience'], 'finite', ['unfinished', tree]],
            'simple':                 tree,
            'perfective-progressive': [['active', 'simple', 'atelic', 'v', 'have'], 'finite', ['finished', 'v', 'be'], ['unfinished', tree]],
            'imperfective':           [['active', 'simple', 'atelic', 'v', 'be'],   'unfinished', 'finite', tree],
            'perfective':             [['active', 'simple', 'atelic', 'v', 'have'], 'finished', 'finite', tree],
        }
        # if (memory['verb'], progress, tense, memory['mood']) == ('go', 'finished', 'present', 'indicative'):
        #     breakpoint()
        return aspect_to_tree[aspect]
        # return [*preverb, *verb, *postverb]
    def voice(self, machine, tree, memory):
        '''creates auxillary verb phrases when necessary to express voice'''
        voice = memory['voice']
        if voice  == 'passive': return [['active', 'v', 'be'],             'finite', ['active', 'finished', tree]]
        if voice  == 'middle':  return [['active', 'implicit', 'v', 'be'], 'finite', ['active', 'finished', tree]]
        return tree
    def definiteness(self, machine, tree, memory):
        '''creates articles when necessary to express definiteness'''
        definiteness = memory['definiteness'] if 'definiteness' in memory else 'indefinite'
        subjectivity = memory['subjectivity']
        nounform = memory['noun-form']
        if definiteness == 'definite' and subjectivity != 'addressee' and nounform in {'common'}: 
            return [['det','the'], tree]
        if definiteness == 'indefinite' and subjectivity != 'addressee' and nounform in {'common'}: 
            return [['det','a'], tree]
        else:
            return tree
    def number(self, machine, tree, memory):
        '''creates articles when necessary to express definiteness'''
        definiteness = memory['definiteness'] if 'definiteness' in memory else 'indefinite'
        subjectivity = memory['subjectivity']
        number = memory['number']
        noun = memory['noun']
        number_lookup = {
            'dual': 'two',
            'trial': 'three',
            'paucal': 'few',
            'superplural': 'lot of',
        }
        if tree[-1] == 'hello':
            return tree
        elif number in number_lookup: 
            if subjectivity=='addressee':
                return [['det', 'you'], ['adj', number_lookup[number]], tree]
            else:
                return [['adj', number_lookup[number]], tree]
        else:
            return tree
    def formality_and_gender(self, machine, tree, memory):
        '''creates pronouns procedurally when necessary to capture distinctions in formality from other languages'''
        formality = memory['formality']
        gender = memory['gender']
        person = memory['person']
        number = memory['number']
        nounform = memory['noun-form']
        nonsingular_3rd_gender_marker = {
            'gendered': '',
            'masculine': '♂',
            'feminine': "♀",
            'neuter': "⚲",
        }
        formal_singular_gender_marker = {
            'masculine': '[sir]',
            'feminine': "[ma'am]",
            'gendered': '[respectfully]',
            'neuter': "[respectfully]",
        }
        formal_nonsingular_gender_marker = {
            'masculine': '[gentlemen]',
            'feminine': "[ladies]",
            'gendered': '[respectfully]',
            'neuter': "[respectfully]",
        }
        gender_marker = {
            ('3','singular'): {
                'formal': {
                    'singular': formal_singular_gender_marker[gender]
                }.get(number, formal_nonsingular_gender_marker[gender])
            }.get(formality, nonsingular_3rd_gender_marker[gender])
        }.get((person, number), '')
        formality_marker = {
            'polite': '[politely]',
            'elevated': '[elevated]',
            'voseo': '[voseo]',
        }.get(formality, '')
        return [tree, 
            gender_marker if 'show-gender' in memory and memory['show-gender'] else '', 
            formality_marker] if nounform == 'personal' else tree


class EnglishRuleSyntax(RuleSyntax):
    def __init__(self, noun_phrase_structure, sentence_structure, content_question_structure=None):
        super().__init__(noun_phrase_structure, sentence_structure, content_question_structure)
    def order_noun_phrase(self, treemap, phrase):
        rules = [element for element in phrase.content if isinstance(element, Rule)]
        nonrules = [element for element in phrase.content if not isinstance(element, Rule)]
        part_to_words = {
            part: [rule
                for rule in rules
                if rule.tag == part]
            for part in 'adposition det n np clause'.split()
        }
        # only one determiner may exist
        # personal possessives
        part_to_words['det'] = (
            [rule
                for rule in rules
                if rule.tag == 'det' and rule.tags['noun-form']=='personal-possessive']
            or part_to_words['det']
        )
        '''
        Adjectives must occur in a certain order, starting with quantities.
        We only represent quantities in this order since quantities are 
        required to represent grammar numbers that do not exist in english,
        so they are the only adjectives that must occur with others in our decks.
        '''
        quantities = {'one', 'two', 'three', 'few', 'many', 'lot of'}
        part_to_words['adj'] = []
        part_to_words['adj'] += [rule
            for rule in rules
            if rule.tag == 'adj' and rule.content[-1] in quantities]
        part_to_words['adj'] += [rule
            for rule in rules
            if rule.tag == 'adj' and rule.content[-1] not in quantities]
        return Rule(phrase.tag, 
            phrase.tags, 
            treemap.map([element
                        for part in self.noun_phrase_structure
                        for element in part_to_words[part]
            ]))


list_tools = ListTools()
rule_tools = RuleTools()
english_list_substitution = EnglishListSubstitution()
regular_english_grammar = RegularEnglishGrammar()
card_formatting = CardFormatting()

english_conjugation_template_lookups = DictLookup(
    'english-conjugation',
    DictKeyIndexing('verb-form'), 
    {
        'finite': parse_any.tokenfield('english-finite-verb', 'verb person number tense aspect'),
        'infinitive': parse_any.tokenfield('english-infinitive-verb', 'verb'),
    })

english_conjugation_population = NestedLookupPopulation(
    english_conjugation_template_lookups, 
    KeyEvaluation('inflection'))

english_language = Language(
    ListSemantics(
        case_usage_population.index(
            case_usage_annotation.annotate(
                tsv_parsing.rows('data/inflection/indo-european/germanic/english/modern/case-usage.tsv'))),
        mood_usage_population.index(
            mood_usage_annotation.annotate(
                tsv_parsing.rows('data/inflection/indo-european/germanic/english/modern/mood-usage.tsv'))),
        aspect_usage_population.index(
            aspect_usage_annotation.annotate(
                tsv_parsing.rows('data/inflection/indo-european/aspect-usage.tsv'))),
        # debug=True,
    ),
    ListGrammar(
        FallbackDictLookup(
            NestedDictLookup(
                english_conjugation_population.index([
                    *finite_annotation.annotate(
                        tsv_parsing.rows('data/inflection/indo-european/germanic/english/modern/irregular-conjugations.tsv')),
                    *finite_annotation.annotate(
                        tsv_parsing.rows('data/inflection/indo-european/germanic/english/modern/regular-conjugations.tsv')),
                ])),
            ProceduralLookup(regular_english_grammar.conjugate),
        ),
        FallbackDictLookup(
            NestedDictLookup(
                declension_population.index([
                    *pronoun_annotation.annotate(
                        tsv_parsing.rows('data/inflection/indo-european/germanic/english/modern/pronoun-declensions.tsv')),
                    *common_noun_annotation.annotate(
                        tsv_parsing.rows('data/inflection/indo-european/germanic/english/modern/common-noun-declensions.tsv')),
                ])),
            ProceduralLookup(regular_english_grammar.decline),
        ),
        FallbackDictLookup(
            NestedDictLookup(
                declension_population.index([
                    *possessive_pronoun_annotation.annotate(
                        tsv_parsing.rows('data/inflection/indo-european/germanic/english/modern/pronoun-possessives.tsv')),
                    *common_noun_annotation.annotate(
                        tsv_parsing.rows('data/inflection/indo-european/germanic/english/modern/adjective-agreements.tsv')),
                ])
            ),
            ProceduralLookup(regular_english_grammar.agree),
        ),
        # debug=True,
    ),
    EnglishRuleSyntax(
        parse_any.tokens('adposition det adj n np clause'),
        parse_any.terms('subject verb direct-object indirect-object adverbial'),
        parse_any.terms('interrogative verb subject direct-object indirect-object adverbial'),
    ),
    {'language-type':'native'},
    list_tools,
    rule_tools,
    RuleFormatting(),
    substitutions = [
        {'cloze': list_tools.unwrap()}, # English serves as a native language here, so it never shows clozes
        {'v': english_list_substitution.verbform}, # English participles are encoded as perfective/imperfective forms and must be handled specially
        {'v': english_list_substitution.mood},     # English uses auxillary verbs (e.g. "mood") to indicate some moods
        {'v': english_list_substitution.tense},    # English uses auxillary verbs ("will") to indicate tense
        {'v': english_list_substitution.aspect},   # English uses auxillary verbs ("be", "have") to indicate aspect
        {'v': english_list_substitution.voice},    # English uses auxillary verbs ("be") to indicate voice
        {'n': english_list_substitution.definiteness},         # English needs annotations to simplify the definition of articles
        {'n': english_list_substitution.number},               # English needs annotations to clarify the numbers of other languages
        {'n': english_list_substitution.formality_and_gender}, # English needs annotations to clarify the formalities and genders of other languages
    ],
    # debug=True,
)

english_orthography = Orthography('latin', english_language)

def mood_context(mood_templates):
    def mood_context_(tags, phrase):
        mood_prephrase = mood_templates[{**tags,'column':'prephrase'}]
        mood_postphrase = mood_templates[{**tags,'column':'postphrase'}]
        voice_prephrase = '[middle voice:]' if tags['voice'] == 'middle' else ''
        return ' '.join([voice_prephrase, mood_prephrase, phrase, mood_postphrase]).replace('∅','')
    return mood_context_

english_mood_context = mood_context(
    mood_population.index(
        mood_annotation.annotate(
            tsv_parsing.rows('data/inflection/indo-european/germanic/english/modern/mood-templates.tsv'))))

native_english_demonstration = LanguageSpecificTextDemonstration(
    english_orthography,
    english_mood_context,
    card_formatting.native_word, 
    [('[the mass of]','')]
)
