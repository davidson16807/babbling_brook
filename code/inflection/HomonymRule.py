"""A node of a syntax tree that stands for several homonyms at once.

`HomonymRule` has the interface of the languages repo's `Rule`: `tag` is its part
of speech, and `content` its words and the `HomonymRule`s of the parts of speech
within it. Unlike a `Rule`, whose `tags` are those it was inflected with, its
`tags` is a list: the tags of this node in each homonym it stands for. An
inflection that is not homonymous is one with a single entry.

It is a class of its own, rather than a `Rule` whose `tags` happen to be a list, so
that a tree of one is never mistaken for a tree of the other.
"""


class HomonymRule:
    def __init__(self, tag, tags, content):
        self.tag = tag
        self.tags = tags        # list of dicts: tagaxis → tag, one per homonym
        self.content = content  # words (strings) and `HomonymRule`s

    def __repr__(self):
        return f'HomonymRule({self.tag!r}, <{len(self.tags)} homonyms>, {self.content!r})'
