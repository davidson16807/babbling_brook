# HUMAN WRITTEN

from itertools import product

from .DialogRule import DialogRule

class RuleInterpretation:

    def __init__(self,
            rule_syntax: RuleSyntax,
            conjugated_tagaxes: list[str], # e.g. ['person', 'number']
            pro_drop_subject:int=0, # 0:no, 1:optional, 2:mandatory
            pro_drop_imperative:int=0, # 0:no, 1:optional, 2:mandatory
            is_free_word_order:bool=False
        ):
        self.rule_syntax = rule_syntax
        self.conjugated_tagaxes = conjugated_tagaxes
        self.pro_drop_subject = pro_drop_subject
        self.pro_drop_imperative = pro_drop_imperative
        self.is_free_word_order = is_free_word_order

    def interpret(self, rule, strict=True):
        subrules = rule.content
        if rule.tag == 'clause':
            verb_phrases = [subrule.tag == 'vp' for subrule in subrules]
            noun_phrases = [subrule for subrule in subrules if subrule.tag == 'np']
            subject_phrases = [phrase for phrase in noun_phrases if subrule.tag['subjectivity'] == 'subject']
            direct_object_phrases = [phrase for phrase in noun_phrases if subrule.tag['subjectivity'] == 'direct-object']
            # there is only one verb phrase
            if len(verb_phrases) != 1:
                return None
            # there is only one subject
            if len(subject_phrases) > 1 or (len(subject_phrases) == 0 and not self.pro_drop_subject):
                if strict: 
                    return None
                elif len(noun_phrases) == 1:
                    return self.rule_syntax.order_clause(Rule(rule.tag, rule.tags, [*noun_phrases, *verb_phrases]))
                else: 
                    return None
            if len(subject_phrases) == 1:
                # subject and verb must match
                subject = subject_phrases[0]
                verb = subject_phrases[0]
                for tagaxis in self.conjugated_tagaxes:
                    if subject.tags[tagaxis] != verb.tags[tagaxis]:
                        return None # TODO: correct the conjugation when `not strict`
            # there is no more than 1 direct object
            if len(direct_object_phrases) > 1:
                return None
            # clauses are ordered
            if (rule.tag == 'clause' and 
                not self.rule_syntax.is_ordered_clause(rule) and 
                not self.is_free_word_order):
                return None if strict else self.rule_syntax.order_clause(rule)
        elif rule.tag == 'np':
            nouns = [subrule for subrule in subrules if subrule.tag == 'n']
            adjectives = [subrule for subrule in subrules if subrule.tag == 'adj']
            if len(nouns) != 1:
                return None
            noun = nouns[0]
            if adjectives:
                if [(adjective, tagaxis)
                    for adjective in adjectives
                    for tagaxis in self.agreement_tagaxes
                    if noun.tags[tagaxis] != adjective.tags[tagaxis]
                ]:
                    return None # TODO: correct the agreement when `not strict`
            # noun phrases are ordered
            if not self.rule_syntax.is_ordered_noun_phrase(rule):
                return None if strict else self.rule_syntax.order_noun_phrase(rule)
        return rule

class DialogRuleInterpretation:
    def __init__(self, rule_interpretation):
        self.rule_interpretation = rule_interpretation

    def interpret(self, rule, strict=True) -> list:
        meanings = [
            self.rule_interpretation.interpret(
                Rule(rule.tag, tagpath, 
                    [self.interpret(subrule, strict=strict) for subrule in rule.content]),
                strict)
            for tagpath in product([subrule.tags for subrule in rule])
        ]
        return [meaning
            for meaning in meanings
            if meaning is not None
        ]

if __name__ == '__main__':

    subject = {'subjectivity': 'subject', 'motion': 'associated', 'role': 'agent', 'case': 'nominative'}
    object_ = {'subjectivity': 'direct-object', 'motion': 'associated', 'role': 'patient', 'case': 'oblique'}
    to      = {'subjectivity': 'adverbial', 'motion': 'acquired', 'role': 'location', 'case': 'oblique'}
    first   = {'person': '1', 'number': 'singular', 'gender': 'masculine', 'noun-form': 'personal'}
    third   = {'person': '3', 'number': 'singular', 'gender': 'masculine', 'noun-form': 'common'}
    givers  = [{'person': p, 'number': n, 'mood': 'indicative'} for p, n in [('1', 'singular'), ('2', 'singular'), ('1', 'plural'), ('2', 'plural'), ('3', 'plural')]]

    I          = DialogRule('np', [{**first, **subject}], [DialogRule('n', [{**first, **subject}], ['I'])])
    me         = DialogRule('np', [{**first, **object_}], [DialogRule('n', [{**first, **object_}], ['me'])])
    give       = DialogRule('vp', givers, [DialogRule('v', givers, ['give'])])
    the_ball   = DialogRule('np', [{**third, **subject}, {**third, **object_}], [DialogRule('det', [{**third, **subject}, {**third, **object_}], ['the']), DialogRule('n', [{**third, **subject}, {**third, **object_}], ['ball'])])
    the_boy    = DialogRule('np', [{**third, **subject}, {**third, **object_}], [DialogRule('det', [{**third, **subject}, {**third, **object_}], ['the']), DialogRule('n', [{**third, **subject}, {**third, **object_}], ['boy'])])
    to_the_boy = DialogRule('np', [{**third, **to}], [DialogRule('adposition', [{**third, **to}], ['to']), DialogRule('det', [{**third, **to}], ['the']), DialogRule('n', [{**third, **to}], ['boy'])])

    correct     = DialogRule('clause', [{}], [I, give, the_ball, to_the_boy])  # 1 strict, 1 lenient
    disordered  = DialogRule('clause', [{}], [give, the_ball, I])              # 0 strict, 1 lenient
    wrong_case  = DialogRule('clause', [{}], [me, give, the_ball])             # 0 strict, 1 lenient
    disagrees   = DialogRule('clause', [{}], [the_boy, give, the_ball])        # 0 strict, 1 lenient
    subjectless = DialogRule('clause', [{}], [give, the_ball])                 # 0 strict, 5 lenient
    nonsense    = DialogRule('clause', [{}], [the_ball, the_boy])              # 0 strict, 0 lenient

    breakpoint()

