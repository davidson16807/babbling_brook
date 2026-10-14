from tools.treemaps import ListTreeMap

class DialogLanguage:
    """
    A `Language` is a "tree mapping" class, analogous to those under nodemaps.py of the `languages` repo.
    As a tree mapping class, a `Language` contains a single method `map()`
    that maps a syntax tree in one representation to another syntax tree in another representation.

    In this case, `ListTreeLanguage` contains a single method `map()`
    that maps a syntax tree that is represented as nested lists of strings storing language-agnostic codes
    to another syntax tree of the same representation that stores translated and inflected words
    of a foreign language that are intended for a player to rearrange to the appropriate word order.
    `ListTreeLanguage` is specially built for "Babbling Brook" to stop just short of applying the word of a recommended syntax.

    `ListTreeLanguage` uses a subset of the injected dependencies found in `Language`:
        semantics:  contains maps from nodes represented as nested lists of language agnostic codes to nodes where the result of grammatical decisions such as aspect or case are stored in memory
        grammar:    contains maps from nodes represented as nested lists of language agnostic codes to nodes represented as nested lists of inflected words as they would appear in a language

    and a subset of settings found in `Language`:
        tags:          a dict mapping tagaxes to their tags
        substitutions: a dict mapping opcodes in the listtree to nodemap functions 
                       of the standard (machine, tree, memory)→tree signature
    """

    RULES = 'clause det adj np vp n v adposition'  # as in `Language.map`

    def __init__(self, semantics, grammar, tags, list_tools, substitutions=[]):
        """Arguments mean what they mean to `Language`, e.g. `english_language.semantics`."""
        self.semantics = semantics
        self.grammar = grammar
        self.tags = tags
        self.list_tools = list_tools
        self.substitutions = substitutions

    def map(self, tree, script, semes={}, substitutions=[], debug=False):
        # The same opcodes as `Language.map`, which defines them inline.
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
        tag_insertion = {opcode: self.semantics.tag({**value, 'script': script}, remove=False)
                         for (opcode, value) in opcode_tags.items()}
        tag_removal = {opcode: self.semantics.tag({**value, 'script': script}, remove=True)
                       for (opcode, value) in opcode_tags.items()}
        pipeline = [
            *[ListTreeMap({**tag_insertion, **substitution}) for substitution in substitutions],
            *[ListTreeMap({**tag_insertion, **substitution}) for substitution in self.substitutions],
            ListTreeMap({
                **tag_insertion,
                'adposition': self.semantics.stock_adposition,
                'v':          self.grammar.conjugate,
                'n':          self.grammar.decline,
                'det':        self.grammar.agree,
                'adj':        self.grammar.agree,
            }),
            ListTreeMap({
                **tag_removal,
                **{tag: self.list_tools.rule() for tag in self.RULES.split()},
            }),
        ]
        for step in pipeline:
            tree = step.map(tree, {**self.tags, 'script': script})
        return tree

