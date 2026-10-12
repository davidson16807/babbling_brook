import re

from .nodes import Rule

"""
"nodes.py" contains functionality used to manipulate individual nodes in a syntax tree
"""

class InflectionFormatting:
    def __init__(self):
        pass
    def is_clozure(self, tags):
        return 'show-clozure' in tags and tags['show-clozure']
    def format(self, text, tags):
        split = re.split(' *[|/,] *', text)
        return split[0] if not self.is_clozure(tags) else '|'.join(split)

class ListSemantics:
    """
    `ListSemantics` is a library of functions that all relevant aspects of semantics in the application,
    where semantics is defined as the language specific grammatical decisions 
    that are made by a speaker to convey their intended language-agnostic meaning.
    In this library, the grammatical decisions made by a speaker are expressed in terms of a single grammatical tag, 
    such as "subjunctive", "ablative", or "perfective".
    The intended meaning of the speaker is expressed in terms of a seme,
    which can indicate many things such as the probability of a event, 
    the motion of a subject with respect to an object, or whether an event has finished.
    Therefore, ListSemantics describes a set of maps:semes→tag, 
    one for each applicable tagaxis such as mood, aspect, or case,
    as well as a map articulate:semes→tags that applies all maps to a dictionary of semes
    """
    def __init__(self, 
            case_usage,
            mood_usage,
            aspect_usage,
            debug=False):
        self.case_usage = case_usage
        self.mood_usage = mood_usage
        self.aspect_usage = aspect_usage
        self.debug = debug
        self.inflection_formatting = InflectionFormatting()
    def case(self, tags):
        return self.case_usage[tags]['case']
    def mood(self, tags):
        return self.mood_usage[tags]['mood']
    def aspect(self, tags):
        return self.aspect_usage[tags]['aspect']
    def augment(self, tags):
        tagaxis_usages = [
            ('case', self.case_usage),
            ('aspect', self.aspect_usage),
            # ('mood', self.mood_usage),
        ]
        return {
            **tags, 
            **{tagaxis: usage[tags][tagaxis] 
               for (tagaxis, usage) in tagaxis_usages
               # if tagaxis not in tags and tagaxis in usage[tags]
               if tags in usage and tagaxis in usage[tags]
            }
        }
    def tag(self, modifications, remove=False, debug=False):
        def _map(machine, tree, memory):
            # if self.debug and 'verb-form' in modifications:
            #     print(modifications['verb-form'])
            arguments = machine.map(tree[1:], self.augment({**memory, **modifications}))
            return arguments if remove else [tree[0], *arguments]
        return _map
    def stock_adposition(self, treemap, content, tags):
        return (content if len(content) > 1
            else [] if tags not in self.case_usage
            else [] if 'preposition' not in self.case_usage[tags]
            else [content[0], 
                self.inflection_formatting.format(self.case_usage[tags]['preposition'], tags)]
        )

class ListGrammar:
    """
    `ListGrammar` is a library of functions that can be used in conjunction with `ListTrees` 
    to perform operations on a syntax tree of lists that encapsulate the grammar of a natural language.
    Examples include word translation, verb conjugation, noun declension, and adjective agreement.
    """
    def __init__(self, 
            conjugation_lookups, 
            declension_lookups, 
            agreement_lookups, 
            omit_code = '—',
            debug=False):
        self.conjugation_lookups = conjugation_lookups
        self.declension_lookups = declension_lookups
        self.agreement_lookups = agreement_lookups
        self.debug = debug
        self.omit_code = omit_code
        self.inflection_formatting = InflectionFormatting()
    def decline(self, treemap, content, tags):
        if 'case' not in tags:
            return self.omit_code
        sememe = {
            **tags, 
            **({'noun':content[1]} if len(content)>1 else {}), 
        }
        return [content[0], 
            None if sememe not in self.declension_lookups
            else self.inflection_formatting.format(self.declension_lookups[sememe], tags)]
    def agree(self, treemap, content, tags):
        if 'case' not in tags:
            return self.omit_code
        sememe = {
            **tags, 
            **({'noun':content[1]} if len(content)>1 else {}), 
        }
        return [content[0], 
            None if sememe not in self.agreement_lookups
            else self.inflection_formatting.format(self.agreement_lookups[sememe], tags)]
    def conjugate(self, treemap, content, tags):
        if any([tagaxis not in tags for tagaxis in 'aspect mood'.split()]):
            return self.omit_code
        sememe = {
            **tags, 
            'verb':content[1],
        }
        return [content[0], 
            None if sememe not in self.conjugation_lookups
            else self.inflection_formatting.format(self.conjugation_lookups[sememe], tags)]
    def stock_modifier(self, treemap, content, tags):
        alttag = {**tags, 'verb-form':'argument'}
        return [content[0], 
            None if alttag not in self.conjugation_lookups
            else self.conjugation_lookups[alttag]]

class RuleSyntax:
    """
    `RuleSyntax` is a library of functions that can be used in conjunction with 
    `RuleTrees` to perform operations on a syntax tree of rules that encapsulate 
    the syntax of a natural language, such as the structuring of clauses and noun phrases.
    It is designed to accomodate sentences in the majority of natural languages, including:
    * typical sentences ("I go to him")
    * negative sentences ("I don't go to him")
    * content questions ("who did?" "where do we go?" etc.)
    * polar questions ("is it so?")
    * languages where word order varies for any of the above (e.g. German)
    * languages where markers for the above are placed between verb and noun phrases (e.g. Spanish)
    * languages where markers for the above are placed as 1st word, 2nd word, last word, etc. (e.g. Latin)
    It does not account for the following:
    * languages where inflected verbs double as polar question markers (e.g. English)
    * languages with multiple obligatory markers for negation (e.g. Middle Egyptian, French)
    * languages with multiple obligatory markers for questions
    Accounting for any of the above requires a custom class that is polymorphic to `RuleSyntax`
    """
    def __init__(self, 
            noun_phrase_structure, 
            sentence_structure, 
            content_question_structure=None, 
            polar_question_structure=None,
            negative_sentence_structure=None, 
            interrogative_position=None,
            polar_particle_position=None):
        # word order in phrases:
        self.noun_phrase_structure = noun_phrase_structure
        # phrase order in sentences:
        self.sentence_structure = sentence_structure
        self.content_question_structure = content_question_structure
        self.polar_question_structure = polar_question_structure
        self.negative_sentence_structure = negative_sentence_structure
        # word order in sentences:
        self.interrogative_position = interrogative_position
        self.polar_particle_position = polar_particle_position
    def order_word_sequence(self, treemap, clause):
        '''
        `order_word_sequence()` orders words without regard to where those words are in syntax trees.
        This can be useful to follow certain rules in language, particularly for question formation.
        For instance, content questions in English move interrogative words like "where" to the front 
        without moving other words like prepositions from the same noun phrase:
            ✓what did the quick brown fox jump over?
            ˣover what did the quick brown fox jump?
        Certain languages indicate polar ("yes/no") questions 
        by inserting a particle after the first word in the sentence.
        For our purposes, this is sufficient to ask polar questions in Latin using the suffix -ne:
            Estne verum?
            Nōnne animadvertis?
            Nihilne in mentem?
        `interrogative_position` and `polar_particle_position` 
        indicate the index of the respective word in the word sequence (typically 0, 1, or -1)
        Setting these to `None` will preserve the existing order.
        '''
        rules = clause.content
        interrogatives = [rule 
            for rule in rules 
            if rule['noun-form'] == 'interrogative']
        polar_question_particles = [rule 
            for rule in rules 
            if rule['subjectivity'] == 'polar-question-marker']
        if self.interrogative_position is not None and interrogatives:
            noninterrogatives = [rule 
                for rule in rules 
                if rule['noun-form'] != 'interrogative']
            rules = (
                noninterrogatives[:self.interrogative_position] + 
                interrogatives + 
                noninterrogatives[self.interrogative_position:]
            )
        elif self.polar_particle_position is not None and polar_question_particles:
            non_polar_question_particles = [rule 
                for rule in rules 
                if rule['subjectivity'] != 'polar-question-marker']
            rules = (
                non_polar_question_particles[:self.polar_particle_position] + 
                polar_question_particles + 
                non_polar_question_particles[self.polar_particle_position:]
            )
        ordered = Rule(clause.tag, clause.tags, rules)
        return ordered
    def order_clause(self, treemap, clause):
        rules = clause.content
        nouns = [phrase for phrase in rules if phrase.tag in {'np'}]
        # enclitic_subjects = [noun for noun in subjects if noun.tags['clitic'] in {'enclitic'}]
        # proclitic_subjects = [noun for noun in subjects if noun.tags['clitic'] in {'proclitic'}]
        interrogatives = [noun 
            for noun in nouns 
            if noun['noun-form'] == 'interrogative']
        noun_lookup = {
            placement: [noun 
                for noun in nouns 
                if noun['subjectivity'] == placement
                and noun['noun-form'] != 'interrogative']
            for placement in '''
                subject direct-object indirect-object 
                adverbial adnominal negation polar-question-marker
                '''.strip().split()
        }
        verbs = [phrase
            for phrase in rules 
            if phrase.tag in {'vp'}]
        phrase_lookup = {
            **noun_lookup,
            'interrogative': interrogatives,
            'verb': verbs,
        }
        structure_name = ('content question' if interrogatives 
            else 'polar question' if clause['evidentiality'] == 'interrogated'
            else 'negative' if clause['polarity'] == 'negative'
            else 'typical sentence')
        structure = {
            'content question': self.content_question_structure,
            'polar question': self.polar_question_structure,
            'negative': self.negative_sentence_structure,
            'typical sentence': self.sentence_structure,
        }[structure_name]
        if not structure:
            raise ValueError(f"No syntax is defined for a {structure_name} in this language")
        ordered = Rule(clause.tag, 
            clause.tags,
            treemap.map([
                phrase
                for phrase_type in structure
                for phrase in phrase_lookup[phrase_type]
            ]))
        return ordered
    def order_noun_phrase(self, treemap, phrase):
        # if 'alt' in str(phrase):
        #     print(phrase)
        #     # breakpoint()
        rules = [element for element in phrase.content if isinstance(element, Rule)]
        nonrules = [element for element in phrase.content if not isinstance(element, Rule)]
        part_to_words = {
            part: [rule
                for rule in rules
                if rule.tag == part]
            for part in 'adposition det adj n np clause'.split()
        }
        return Rule(phrase.tag, 
            phrase.tags, 
            treemap.map([element
                        for part in self.noun_phrase_structure
                        for element in part_to_words[part]
            ]))

class RuleFormatting:
    """
    `RuleFormatting` is a library of functions that can be used in conjunction with `RuleTrees` 
    to cast a syntax tree to a string of natural language.
    """
    def __init__(self, affix_delimiter='-', diagnostics=False):
        self.affix_delimiter = affix_delimiter
        self.affix_regex = re.compile('\s*-\s*')
        self.space_regex = re.compile('\s+')
        self.empty_regex = re.compile('∅')
        self.diagnostics = diagnostics
    def default(self, treemap, element):
        newline = '&#xA;'
        clozure = lambda rule: 'show-clozure' in rule.tags and rule.tags['show-clozure']
        parenthesis = lambda rule: 'show-parentheses' in rule.tags and rule.tags['show-parentheses']
        brackets = lambda rule: 'show-brackets' in rule.tags and rule.tags['show-brackets']
        def format_note_section(lookup, tags):
            return newline.join([
                f'{key} : {lookup[key]}'
                for key in tags
                if key in lookup])
        def format_notes(lookup):
            return (newline*2).join([
                format_note_section(lookup, 'mood evidentiality confidence'.split()),
                format_note_section(lookup, 'aspect progress'.split()),
                format_note_section(lookup, 'verb verb-form completion strength voice tense polarity'.split()),
                format_note_section(lookup, 'case subjectivity valency motion role'.split()),
                format_note_section(lookup, 'noun noun-form definiteness person number gender animacy clusivity formality clitic partitivity degree'.split()),
                format_note_section(lookup, 'language-type script'.split()),
                format_note_section(lookup, 'possessor-person possessor-number possessor-gender possessor-clusivity possessor-formality'.split()),
            ])
        def format_rule(rule):
            tokens = []
            was_clozed = clozure(rule)
            was_parens = parenthesis(rule)
            was_brackets = brackets(rule)
            for subrule in rule.content:
                if type(subrule) == Rule:
                    # TODO: fix this up into functions that operate 
                    if not was_clozed and clozure(subrule):
                        tokens.append('{{c1::')
                        was_clozed = True
                    if was_clozed and not clozure(subrule):
                        tokens.append('}}')
                        was_clozed = False
                    if not was_parens and parenthesis(subrule):
                        tokens.append('(')
                        was_parens = True
                    if was_parens and not parenthesis(subrule):
                        tokens.append(')')
                        was_parens = False
                    if not was_brackets and brackets(subrule):
                        tokens.append('[')
                        was_brackets = True
                    if was_brackets and not brackets(subrule):
                        tokens.append(']')
                        was_brackets = False
                text = treemap.map(subrule)
                tokens.append('[MISSING]' if text is None else str(text) )
            if was_clozed and not clozure(rule):
                tokens.append('}}')
            if was_parens and not parenthesis(rule):
                tokens.append(')')
            if was_brackets and not brackets(rule):
                tokens.append(']')
            body = " ".join(tokens)
            '''
            Do not render the card if a user would be tested to identify
            the contents a clozure whose translation is unknown,
            return '❕' to signal that the card should not be rendered
            '''
            if ('…' in body) and clozure(rule):
                return '❕'
            elif self.diagnostics:
                return f'<span title="{format_notes(rule.tags)}">{body}</span>'
            else: 
                return body
        result ={
            str:        lambda text: text,
            Rule:       lambda rule: format_rule(rule),
            type(None): lambda none: f'[MISSING]',
        }[type(element)](element)
        result = self.affix_regex.sub(self.affix_delimiter, result)
        result = self.space_regex.sub(' ', result)
        result = self.empty_regex.sub('', result)
        result = result.strip()
        return result
    def cloze(self, treemap, rule):
        return '{{c'+str(1)+'::'+' '.join(str(treemap.map(element)) for element in rule.content)+'}}'
    def implicit(self, treemap, rule):
        return '['+str(' '.join([str(treemap.map(element)) for element in rule.content]))+']'
    def parentheses(self, treemap, rule):
        return '('+str(' '.join([str(treemap.map(element)) for element in rule.content]))+')'

class ListTools:
    def __init__(self):
        pass
    def tag(self, modifications, remove=False):
        def _map(machine, tree, memory):
            arguments = machine.map(tree[1:], {**memory, **modifications})
            return arguments if remove else [tree[0], *arguments]
        return _map
    def rule(self):
        def flatten(x): 
            return [xij for xi in x for xij in flatten(xi)] if isinstance(x, list) else [x]
        def _map(machine, tree, memory):
            return Rule(tree[0], memory, flatten(machine.map(tree[1:], memory)))
        return _map
    def replace(self, *functions):
        def _map(machine, tree, memory):
            return [*functions, *machine.map(tree[1:], memory)]
        return _map
    def constant(self, *values):
        def _map(machine, tree, memory):
            return [*values]
        return _map
    def postprocess(self, function):
        def _map(machine, tree, memory):
            return [function, tree[0], *machine.map(tree[1:], memory)]
        return _map
    def preprocess(self, function):
        def _map(machine, tree, memory):
            return [tree[0], function, *machine.map(tree[1:], memory)]
        return _map
    def wrap(self, function):
        def _map(machine, tree, memory):
            return [function, tree[0], *machine.map(tree[1:], memory)]
        return _map
    def unwrap(self):
        def _map(machine, tree, memory):
            return machine.map(tree[1:], memory)
        return _map
    def prune(self):
        def _map(machine, tree, memory):
            return []
        return _map
    def memory_to_preprocess(lookup):
        def _map(self, machine, tree, memory):
            return [*lookup[memory], tree[0], *machine.map(tree[1:], memory)]
        return _map
    def memory_to_postprocess(lookup):
        def _map(self, machine, tree, memory):
            return [tree[0], *lookup[memory], *machine.map(tree[1:], memory)]
        return _map

class RuleTools:
    def __init__(self):
        pass
    def flatten(self, tags):
        def _map(treemap, rule):
            return Rule(
                rule.tag,
                rule.tags,
                [descendant 
                    for child in rule.content
                    for descendant in treemap.map(child).content]
            )
        return _map