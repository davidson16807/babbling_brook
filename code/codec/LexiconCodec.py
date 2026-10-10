"""Sectioned TSV for a `Lexicon`, framed like `.game` files.

One `# inflections` row per tagpoint. Rows sharing a lexeme and token texts are
interpretations of the same inflection, and decode into one `Inflection`.
Token parts and texts are `|`-delimited (a token may contain spaces, as in
"away from"); tags are space-delimited `tagaxis=tag` pairs.
"""
from .ComposedCodec import ComposedCodec
from .ConcatenatedContainerCodec import ConcatenatedContainerCodec
from .DelimitedStringsCodec import DelimitedStringsCodec
from .PrimitiveListCodec import PrimitiveListCodec
from .ZippedCodec import ZippedCodec
from .ExplorerStateCodec import ExplorerRecordTableCodec, ExplorerTableCodec
from ..model.Lexicon import Inflection, Lexeme, Lexicon, Token, tagpoint


class LexiconListCodec:
    item_count = 1

    def encode(self, lexicon):
        lexemes = [(lexeme.id, lexeme.part, lexeme.display, lexeme.default)
                   for lexeme in lexicon.lexemes.values()]
        inflections = [
            (lexeme.id,
             '|'.join(token.part for token in inflection.tokens),
             '|'.join(token.text for token in inflection.tokens),
             ' '.join(f'{axis}={tag}' for axis, tag in point))
            for lexeme in lexicon.lexemes.values()
            for inflection in lexeme.inflections
            for point in inflection.tagpoints
        ]
        return [{'language': lexicon.language}, lexemes, inflections]

    def decode(self, code):
        header, lexemes, rows = code
        fibers = {}  # (lexeme, token tuple) -> tagpoints, in first-seen order
        for lexeme, parts, texts, tags in rows:
            parts, texts = parts.split('|'), texts.split('|')
            if len(parts) != len(texts):
                raise ValueError(f'{lexeme!r}: {len(parts)} token parts for {len(texts)} tokens')
            tokens = tuple(Token(part, text) for part, text in zip(parts, texts))
            point = tagpoint(dict(pair.split('=', 1) for pair in tags.split()))
            fibers.setdefault((lexeme, tokens), []).append(point)
        decoded = {}
        for id, part, display, default in lexemes:
            if id in decoded:
                raise ValueError(f'Duplicate lexeme {id!r}')
            inflections = tuple(Inflection(tokens, tuple(points))
                                for (owner, tokens), points in fibers.items() if owner == id)
            if not inflections:
                raise ValueError(f'Lexeme {id!r} has no inflections')
            lexeme = Lexeme(id, part, display, default, inflections)
            lexeme.inflection(default)  # raises if the default is not an inflection
            decoded[id] = lexeme
        unknown = {owner for owner, _ in fibers} - decoded.keys()
        if unknown:
            raise ValueError(f'Inflections for undeclared lexemes: {", ".join(sorted(unknown))}')
        return Lexicon(header['language'], decoded)


def LexiconStringCodec(table_delimiter='\n\n', table_regex_delimiter=r'\n\t*\n'):
    def strings(count):
        return ConcatenatedContainerCodec(tuple, *(PrimitiveListCodec(str) for _ in range(count)))
    return ComposedCodec(
        LexiconListCodec(),
        ZippedCodec(
            ExplorerTableCodec('# lexicon\n# key\tvalue', PrimitiveListCodec(str), PrimitiveListCodec(str)),
            ExplorerRecordTableCodec('# lexemes\n# lexeme\tpart\tdisplay\tdefault', strings(4)),
            ExplorerRecordTableCodec('# inflections\n# lexeme\tparts\ttokens\ttags', strings(4)),
        ),
        DelimitedStringsCodec(table_delimiter, table_regex_delimiter, postfixed=True),
    )
