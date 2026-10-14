"""Combine inflections that read the same into one `HomonymRule` tree that keeps every interpretation.

Homonyms such as "give" (1st or 2nd person singular, or any person plural) read
alike but were inflected with different tagpoints. `group` turns the languages
repo's `Rule` trees into `HomonymRule` trees, one per reading: its `content` is that
of any one of the homonyms, and the `tags` of each node list that node's tags in
each of them. Combining needs homonyms of the same shape, so that each position
holds the same part of speech in all of them; otherwise it raises.
"""
from .HomonymRule import HomonymRule


class HomonymRules:
    def __init__(self, formatting):
        """`formatting` casts a `HomonymRule` tree to text; see HomonymRuleFormatting.py."""
        self.formatting = formatting

    def group(self, rules) -> list:
        """One `HomonymRule` tree per way `rules` read, in the order each reading first occurs."""
        readings = {}
        for rule in rules:
            homonym = self.homonym(rule)
            readings.setdefault(self.formatting.format(homonym), []).append(homonym)
        return [self.combine(homonyms) for homonyms in readings.values()]

    def homonym(self, rule):
        """The `HomonymRule` tree of one `Rule` tree: a single homonym."""
        if not hasattr(rule, 'content'):
            return rule  # a word, or None
        return HomonymRule(rule.tag, [rule.tags], [self.homonym(child) for child in rule.content])

    def combine(self, nodes):
        """One `HomonymRule` tree for `HomonymRule` trees that read the same."""
        first = nodes[0]
        if not isinstance(first, HomonymRule):
            return first
        if any(not isinstance(node, HomonymRule) or node.tag != first.tag
               or len(node.content) != len(first.content) for node in nodes):
            raise ValueError(f'Homonyms of {self.formatting.format(first)!r} differ in shape')
        return HomonymRule(first.tag, [tags for node in nodes for tags in node.tags],
                           [self.combine([node.content[index] for node in nodes])
                            for index in range(len(first.content))])
