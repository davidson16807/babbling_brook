"""A language that maps a syntax tree to a list tree of inflected words, instead of to text.

`ListTreeLanguage` has the interface of the languages repo's `Language`: a `tags`
attribute and `map(tree, script, semes, substitutions)`, so `Orthography` and the
repo's demonstrations accept it. Its `map` runs the stages of `Language.map` that
inflect: the substitutions (which add articles, adpositions, and auxiliaries), then
semantics and grammar (adpositions, declension, conjugation, agreement), then the
removal of tag opcodes. It leaves out what follows in `Language.map`: conversion to
`Rule` trees, syntax, and formatting. Those order words and join them into text,
and in the dialog the player orders the words.

This module imports library modules: import it through
`adapter.LanguagesLibrary.import_module`.
"""
from tools.treemaps import ListTreeMap


class ListTreeLanguage:
    def __init__(self, semantics, grammar, tags, substitutions=[]):
        """Arguments mean what they mean to `Language`, e.g. `english_language.semantics`."""
        self.semantics = semantics
        self.grammar = grammar
        self.tags = tags
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
            ListTreeMap(tag_removal),
        ]
        for step in pipeline:
            tree = step.map(tree, {**self.tags, 'script': script})
        return tree

