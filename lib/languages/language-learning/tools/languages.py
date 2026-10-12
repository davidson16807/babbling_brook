from collections import defaultdict

from .treemaps import ListTreeMap, RuleTreeMap

class Language:
    """
    A `Language` is a "tree mapping" class, analogous to those found under nodemaps.py.
    As a tree mapping class, `Language` is a category with at least one arrow
    that maps a syntax tree in one representation to another syntax tree in another representation.
    In this case, `Language` contains a single method `map()`
    that maps a syntax tree that is represented as nested lists storing language-agnostic codes
    to a syntax tree that is represented as a string containing one possible translation 
    of the meaning of the input tree to the natural language that is represented by `Language`.

    A `Language` can alternately be defined in a bottom-up way as a series of "node mapping" class instances that contain maps for individual nodes on trees
    These node mapping class instances can be seen in the parameters of the constructor for `Language`:
        semantics:  contains maps from nodes represented as nested lists of language agnostic codes to nodes where the result of grammatical decisions such as aspect or case are stored in memory
        grammar:    contains maps from nodes represented as nested lists of language agnostic codes to nodes represented as nested lists of inflected words as they would appear in a language
        syntax:     contains maps from nodes represented as nested and unordered `Rule` objects to nodes represented as nested `Rule` objects ordered as they would appear according to language ordering rules (e.g. sentence structure)
        formatting: contains maps between nodes represented as nested lists of strings indicating how constructs such as Anki "cloze" statements should be rendered as strings
        list_tools:      contains maps of nodes represented as nested lists of strings without concern to what the strings represent
        rule_tools:      contains maps of nodes represented as nested rules without concern to what the rules represent
    """
    def __init__(self, 
            semantics,
            grammar,
            syntax,
            tags,
            list_tools,
            rule_tools,
            formatting,
            substitutions=[],
            debug=False):
        self.semantics = semantics
        self.grammar = grammar
        self.syntax = syntax
        self.tags = tags
        self.list_tools = list_tools
        self.rule_tools = rule_tools
        self.formatting = formatting
        self.substitutions = substitutions
        self.debug = debug
    def map(self, tree, script, semes={}, substitutions=[], debug=False):
        opcode_tags = {
            'cloze':       {'show-clozure': True},
            'parentheses': {'show-parentheses': True},
            'implicit':    {'show-brackets': True},
            'informal':    {'formality': 'informal'},
            'indicative':  {'mood': 'indicative'},
            'present':     {'tense': 'present'},
            'perfective':  {'aspect': 'perfective'},
            'imperfective':{'aspect': 'imperfective'},
            'progressive': {'aspect': 'imperfective'},
            'simple':      {'aspect': 'simple'},
            'finished':    {'progress': 'finished'},
            'unfinished':  {'progress': 'unfinished'},
            'atelic':      {'progress': 'atelic'},
            'active':      {'voice': 'active'},
            'passive':     {'voice': 'passive'},
            'middle':      {'voice': 'middle'},
            'infinitive':  {'verb-form': 'infinitive'},
            'finite':      {'verb-form': 'finite'},
            'participle':  {'verb-form': 'participle'},
            'common':      {'noun-form': 'common'},
            'personal':    {'noun-form': 'personal'},
            'agent':       {'role':'agent'},
            'force':       {'role':'force'},
            'patient':     {'role':'patient'},
            'theme':       {'role':'theme'},
            'experiencer': {'role':'experiencer'},
            'stimulus':    {'role':'stimulus'},
            'predicate':   {'role':'predicate'},
            'predicand':   {'role':'predicand'},
            'subject':        {'subjectivity':'subject'},
            'direct-object':  {'subjectivity':'direct-object'},
            'indirect-object':{'subjectivity':'indirect-object'},
            'adverbial':  {'subjectivity':'adverbial'},
            'adnominal':  {'subjectivity':'adnominal'},
            'addressee':      {'subjectivity':'addressee'},
            'common-possessive':   {'noun-form': 'common-possessive'},
            'personal-possessive': {'noun-form': 'personal-possessive'},
            'definite': {'definiteness': 'definite'},
            'indefinite': {'definiteness': 'indefinite'},
            'adefinite': {'definiteness': 'adefinite'},
            **semes
        }
        debug =  self.debug
        tag_insertion = {opcode:self.semantics.tag({**value,'script':script}, remove=False) for (opcode, value) in opcode_tags.items()}
        tag_removal   = {opcode:self.semantics.tag({**value,'script':script}, remove=True, debug=debug)  for (opcode, value) in opcode_tags.items()}
        rules = 'clause det adj np vp n v adposition'
        pipeline = [
            *[ListTreeMap({**tag_insertion, **substitution}) for substitution in substitutions],      # deck specific substitutions
            *[ListTreeMap({**tag_insertion, **substitution}) for substitution in self.substitutions], # language specific substitutions
            ListTreeMap({
                **tag_insertion, 
                'adposition': self.semantics.stock_adposition,
                'v':                self.grammar.conjugate,
                'n':                self.grammar.decline,
                'det':              self.grammar.agree,
                'adj':              self.grammar.agree,
            }),
            ListTreeMap({
                **tag_removal,
                **{tag:self.list_tools.rule() for tag in rules.split()},
            }),
            RuleTreeMap({
                'clause':  self.syntax.order_clause,
                'np':      self.syntax.order_noun_phrase,
            }),
            RuleTreeMap(defaultdict(lambda: self.rule_tools.flatten)),
            RuleTreeMap({
                'clause': self.syntax.order_word_sequence
            }),
            RuleTreeMap({
                **{tag:self.formatting.default for tag in rules.split()},
            }),
        ]
        if debug:
            print(f'input:')
            print(tree)
        for i, step in enumerate(pipeline):
            tree = step.map(tree, {**self.tags, 'script': script})
            if debug:
                print(f'step {i} results:')
                print(tree)
        return tree
