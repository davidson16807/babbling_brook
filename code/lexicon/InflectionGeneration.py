"""Generate the inflections of a traversal, as `DeckGeneration` generates a deck's cards.

The public interface is `DeckGeneration`'s: `InflectionGeneration(omit_codes)` and
`generate(demonstrations, traversal, tag_templates={})`, which calls each
demonstration with `(tags, tag_templates)` for every tagpoint of the traversal and
skips results containing an omit code. Where `DeckGeneration` joins demonstrations
into a card string, this concatenates their tokens; and it yields each tagpoint
with its tokens, since the inflection grid needs to know what every text can mean.
"""


class InflectionGeneration:
    def __init__(self, omit_codes=['—', '❕', '❔']):
        self.omit_codes = omit_codes

    def generate(self,
            demonstrations,
            traversal,
            tag_templates={},
        ):
        for tuplekey in traversal:
            tags = traversal.indexing.dictkey(tuplekey)
            tokens = tuple(token
                for demonstration in demonstrations
                for token in demonstration(tags, tag_templates))
            if all(symbol not in token.text for token in tokens for symbol in self.omit_codes):
                yield tags, tokens
