"""Addresses constituents and their children by label. `ROOT`, the empty address, addresses
the root itself: the statement, or any constituent on its own. There is one address
language, and it owns no rules of arrangement.

A constituent's children are the children of its `Rule` that read as something (a noun
phrase's adposition, article, noun, ...), followed by the constituents added to it (the
statement's phrases, a noun phrase's adjectives). A label names a child as the `index`th
child of its part of speech, counting generated children first and added ones in their order
of addition. In "the red ball", whose `Rule` is np{adposition{∅} det{the} n{ball}} and to which
"red" was added:

    ('det', 0) is "the"        ('n', 0) is "ball"        ('adj', 0) is "red"

The adposition reads as nothing ('∅' marks a linguistic zero), so it is no child. An address
is the labels from the root down to a child: (('np', 1), ('adj', 0)) is the first adjective
of the statement's second noun phrase.

Labels are counted, never stored. Constituents are immutable, so the count for each is
cached, a pure function of the constituent. `rule` casts what an address holds back to a `Rule`,
which is all the dialog hands out: labels never leave it.
"""
from dataclasses import replace
from functools import lru_cache

from .DialogState import Constituent


class ConstituentAddresses:
    ROOT = ()

    def __init__(self, cache_size=4096):
        self._count = lru_cache(maxsize=cache_size)(self._uncached_count)

    def child(self, address, label):
        return (*address, label)

    def parent(self, address):
        return address[:-1]

    def label(self, address):
        """The last label of an address: what its parent calls it."""
        return address[-1]

    def is_ancestor(self, ancestor, descendant):
        return len(descendant) > len(ancestor) and descendant[:len(ancestor)] == ancestor

    def generated(self, root, address):
        """The addresses of the children the constituent at this address was generated with, in order."""
        node = self.resolve(root, address)
        return () if not isinstance(node, Constituent) else tuple(
            self.child(address, label) for label in self._count(node)[0])

    def added(self, root, address):
        """The addresses of the children added to the constituent at this address, in their order of addition."""
        node = self.resolve(root, address)
        return () if not isinstance(node, Constituent) else tuple(
            self.child(address, label) for label in self._count(node)[1])

    def resolve(self, root, address):
        """The constituent or generated child at this address, else None."""
        node = root
        for label in address:
            if not isinstance(node, Constituent):
                return None
            node = self._count(node)[2].get(label)
        return node

    def replace(self, root, address, replacement):
        """The root with the constituent at this address replaced by `replacement`."""
        if address == self.ROOT:
            return replacement
        index = self._count(root)[1].index(address[0])
        child = self.replace(root.added[index], address[1:], replacement)
        return replace(root, added=(*root.added[:index], child, *root.added[index + 1:]))

    def rule(self, root, address=ROOT):
        """The `Rule` of the constituent at this address, with its children, generated and added,
        in the player's order; a generated child as it is."""
        node = self.resolve(root, address)
        if not isinstance(node, Constituent):
            return node
        rule = node.inflection
        return type(rule)(rule.tag, rule.tags, [self.rule(root, self.child(address, label))
                                                for label in node.arrangement])

    def all(self, root):
        """The address of every child under the root, in label order, each before its own children."""
        result = []
        def visit(address):
            for child in (*self.generated(root, address), *self.added(root, address)):
                result.append(child)
                visit(child)
        visit(self.ROOT)
        return tuple(result)

    def _reads(self, node):
        if node is None:
            return True  # a missing inflection
        if isinstance(node, str):
            return bool(node.replace('∅', '').strip())
        return any(self._reads(child) for child in node.content)

    def _uncached_count(self, constituent):
        """(generated labels, added labels, label → child) of the constituent."""
        rule, counts = constituent.inflection, {}
        def label(part):
            counts[part] = counts.get(part, 0) + 1
            return (part, counts[part] - 1)
        generated = [(rule.tag if child is None or isinstance(child, str) else child.tag, child)
                     for child in rule.content if self._reads(child)]
        generated_labels = tuple(label(part) for part, _ in generated)
        added_labels = tuple(label(child.inflection.tag) for child in constituent.added)
        children = {**dict(zip(generated_labels, (child for _, child in generated))),
                    **dict(zip(added_labels, constituent.added))}
        return generated_labels, added_labels, children
