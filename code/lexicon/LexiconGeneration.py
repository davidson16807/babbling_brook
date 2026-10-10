"""Build a `Lexicon` by rendering dictstore traversals with the languages repo.

This plays the part that `DeckGeneration` plays for the repo's flashcards. A deck
demonstrates each tagpoint of a traversal as a card; a lexicon renders each
tagpoint to tokens with `Language.map`, then groups tagpoints by the text they
render to. That grouping is the bundle text → tagpoints, so a homonym such as
English "give" keeps every interpretation.

This module imports library modules: import it through
`adapter.LanguagesLibrary.import_module`.
"""
import copy
import re
from dataclasses import dataclass

from tools.dictstores import DictSet
from tools.indexing import DictTupleIndexing
from tools.nodemaps import ListTools
from tools.nodes import Rule
from tools.parsing import ListParsing

from ..model.Lexicon import Inflection, Lexeme, Lexicon, Token, tagpoint


class TokenFormatting:
    """Takes the place of a `Language`'s `RuleFormatting`: ordered (part, text) tokens, not text."""
    def default(self, treemap, element):
        tokens = []
        def walk(node, parent):
            if isinstance(node, Rule):
                for child in node.content:
                    walk(child, node)
            elif node is not None:
                tokens.append((parent.tag if parent is not None else '', str(node)))
        walk(element, None)
        return tokens


@dataclass(frozen=True)
class PartOfSpeech:
    """How to render and present the lexemes of one part of speech."""
    part: str              # 'noun', 'pronoun', 'verb', or 'adjective'
    tree: str              # `ListParsing` syntax tree; tags apply under its 'test' label
    template: dict         # tags shared by every tagpoint, like the scripts' tag_templates['test']
    parts: frozenset       # token parts that belong to the lexeme, e.g. 'det' for a noun phrase
    default: DictSet       # selects the inflection a newly placed word starts with


class LexiconGeneration:
    def __init__(self, language, defaults, script='latin'):
        self.language = copy.copy(language)
        self.language.formatting = TokenFormatting()
        self.defaults = defaults          # a DictSpace that fills every unspecified tagaxis
        self.script = script
        self.parsing = ListParsing()
        self.list_tools = ListTools()

    def tokens(self, speech: PartOfSpeech, tags: dict) -> tuple[Token, ...]:
        """Render one tagpoint, as `LanguageSpecificTextDemonstration` does, keeping tokens."""
        tags = {**tags, **speech.template}
        substitutions = [{key: self.list_tools.replace(tags[key])}
                         for key in ('noun', 'adjective', 'verb') if key in tags]
        rendered = self.language.map(self.parsing.parse(speech.tree), self.script,
                                     {'test': tags}, substitutions)
        result = []
        for part, text in rendered:
            part = 'v' if part == 'vp' else part  # auxiliaries ("will") sit directly in the vp
            # As `RuleFormatting.default` does: drop the empty marker, collapse spaces.
            text = re.sub(r'\s+', ' ', text.replace('∅', '')).strip()
            if part in speech.parts and text:
                result.append(Token(part, text))
        return tuple(result)

    def rows(self, speech: PartOfSpeech, traversal):
        """(point, tags, tokens) for each tagpoint of `traversal`, in traversal order.

        `point` has only the traversal's own tagaxes; `tags` is completed by the defaults.
        """
        completed = self.defaults.override(traversal)
        for tuplekey in completed:
            tags = completed.indexing.dictkey(tuplekey)
            point = {axis: tags[axis] for axis in traversal.indexing}
            yield point, tags, self.tokens(speech, tags)

    def lexeme(self, speech: PartOfSpeech, traversal, id: str, listing: DictSet = None) -> Lexeme:
        """One lexeme from every tagpoint of `traversal`.

        Its inventory text is its default inflection, or, given `listing`, the first
        three texts whose tags it selects (as in "I, you, he…").
        """
        fibers, default, listed = {}, None, []
        for point, tags, tokens in self.rows(speech, traversal):
            if not tokens:
                continue
            fibers.setdefault(tokens, []).append(tagpoint(point))
            if default is None and tags in speech.default:
                default = tokens
            if listing is not None and tags in listing and tokens not in listed:
                listed.append(tokens)
        if default is None:
            raise ValueError(f'{speech.default.name} selects no inflection of {id!r}')
        inflections = tuple(Inflection(tokens, tuple(points)) for tokens, points in fibers.items())
        text = lambda tokens: ' '.join(token.text for token in tokens)
        display = ', '.join(text(tokens) for tokens in listed[:3]) + '…' if listing is not None else text(default)
        return Lexeme(id, speech.part, display, text(default), inflections)

    def lexemes(self, speech: PartOfSpeech, traversal, key: str) -> list[Lexeme]:
        """One lexeme per value of the tagaxis `key` (e.g. 'noun') in `traversal`."""
        values = list(dict.fromkeys(traversal.indexing.dictkey(tuplekey)[key] for tuplekey in traversal))
        return [self.lexeme(speech, traversal & self.only(key, value), value) for value in values]

    def only(self, key, value) -> DictSet:
        return DictSet(f'{key}={value}', DictTupleIndexing([key]), [{key: value}])

    def lexicon(self, language: str, lexemes) -> Lexicon:
        lexemes = list(lexemes)
        duplicates = {lexeme.id for lexeme in lexemes if [l.id for l in lexemes].count(lexeme.id) > 1}
        if duplicates:
            raise ValueError(f'Duplicate lexemes: {", ".join(sorted(duplicates))}')
        return Lexicon(language, {lexeme.id: lexeme for lexeme in lexemes})
