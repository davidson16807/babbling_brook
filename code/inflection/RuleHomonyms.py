"""Combine inflections that read the same into one `Rule` tree that keeps every interpretation.

Homonyms such as "give" (1st or 2nd person singular, or any person plural) read
alike but were inflected with different tagpoints. `group` returns one `Rule` tree
per reading. Its `content` is that of any one of them, and the `tags` of each node
is a list: the tags that node was inflected with, in each of the homonyms.

The result is a `Rule`, not a subclass, since the languages repo's `RuleFormatting`
recognizes `Rule`s by exact type. Merging needs homonyms of the same shape, so that
each position holds the same part of speech in all of them; otherwise it raises.
"""


class RuleHomonyms:
    def __init__(self, text):
        """`text(node)` is what a `Rule` tree, or a word in one, reads as."""
        self.text = text

    def group(self, rules) -> list:
        """One merged `Rule` tree per way `rules` read, in the order each reading first occurs."""
        readings = {}
        for rule in rules:
            readings.setdefault(self.text(rule), []).append(rule)
        return [self.merge(homonyms) for homonyms in readings.values()]

    def merge(self, nodes):
        """One `Rule` tree for `Rule` trees that read the same, listing the tags of each."""
        first = nodes[0]
        if not hasattr(first, 'content'):
            if any(self.text(node) != self.text(first) for node in nodes):
                raise ValueError(f'Homonyms read differently: {nodes}')
            return first
        if any(getattr(node, 'tag', None) != first.tag or len(node.content) != len(first.content)
               for node in nodes):
            raise ValueError(f'Homonyms of {self.text(first)!r} differ in shape')
        content = [self.merge([node.content[index] for node in nodes]) for index in range(len(first.content))]
        return type(first)(first.tag, [node.tags for node in nodes], content)
