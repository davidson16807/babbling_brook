"""Addresses constituents by the labels of their children.

The empty address, `ROOT`, addresses the root it is resolved in: the statement, or any
constituent on its own. (('np', 1),) addresses the statement's second noun phrase, and
(('np', 1), ('adj', 0)) that phrase's first adjective. A child a phrase was generated
with, such as its article, is addressed the same way, as (('np', 1), ('det', 0)). There
is one address language, and it knows nothing of how constituents are rearranged: it
only resolves, replaces, and relates addresses.

A constituent's children are the children of its `Rule` that read as something (a noun
phrase's adposition, article, noun, ...), followed by the constituents added to it. A
label names each child as the `index`th child of its part of speech, counting generated
children first and added ones in their order of addition, so ('det', 0) is "the" in "the
ball". Labels are not stored but counted from the `Rule` and the added constituents;
since constituents are immutable, the count for each is cached, a pure function of the
constituent. Only `tag` and `content` of a `Rule` are read.
"""
from dataclasses import replace
from functools import lru_cache

from .DialogState import Constituent


class ConstituentAddresses:
    """
    `ConstituentAddresses` is a category whose objects are addresses and whose arrows
    relate an address to its parent, its last label, and its children, and resolve or
    replace what an address addresses within a root.
    """
    ROOT = ()

    def __init__(self, cache_size=4096):
        self._labelled = lru_cache(maxsize=cache_size)(self._label)

    def child(self, address, label):
        return (*address, label)

    def parent(self, address):
        return address[:-1]

    def label(self, address):
        """The last label of the address: what its parent calls it."""
        return address[-1]

    def children(self, root, address):
        """The addresses of the children of the constituent at this address, in label order:
        those it was generated with, then those added to it, in their order of addition."""
        node = self.resolve(root, address)
        if not isinstance(node, Constituent):
            return ()
        generated, added = self._labels(node)
        return tuple(self.child(address, label) for label in (*generated, *added))

    def resolve(self, root, address):
        """The constituent or generated child at this address, else None."""
        node = root
        for label in address:
            if not isinstance(node, Constituent):
                return None
            node = self._children(node).get(label)
        return node

    def replace(self, root, address, replacement):
        """The root with the added constituent at this address replaced by `replacement`."""
        if address == self.ROOT:
            return replacement
        index = self._labels(root)[1].index(address[0])
        child = self.replace(root.added[index], address[1:], replacement)
        return replace(root, added=(*root.added[:index], child, *root.added[index + 1:]))

    def all(self, root):
        """The address of every child under the root, each before those of its children."""
        result = []
        def visit(address):
            for child in self.children(root, address):
                result.append(child)
                visit(child)
        visit(self.ROOT)
        return tuple(result)

    def is_ancestor(self, ancestor, descendant):
        return len(descendant) > len(ancestor) and descendant[:len(ancestor)] == ancestor

    def _reads(self, node) -> bool:
        """Whether a child of a `Rule` reads as something; '∅' marks a linguistic zero, and a
        missing inflection (None) reads as '[MISSING]'."""
        if node is None:
            return True
        if isinstance(node, str):
            return bool(node.replace('∅', '').strip())
        return any(self._reads(child) for child in node.content)

    def _label(self, constituent):
        """(generated labels, added labels, label → child) for the constituent: each child labelled as the
        `index`th child of its part, counting generated children first, then added ones in their order."""
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

    def _labels(self, constituent) -> tuple[tuple, tuple]:
        """(the labels of the generated children, the labels of the added children), in their orders."""
        generated, added, _ = self._labelled(constituent)
        return generated, added

    def _children(self, constituent) -> dict:
        """Each label of the constituent → its child: a `Rule` it was generated with, or a `Constituent` added to it."""
        return self._labelled(constituent)[2]
