"""Addresses constituents by the labels of their children.

The empty address, `ROOT`, addresses the statement; (('np', 1),) addresses its
second noun phrase, and (('np', 1), ('adj', 0)) that phrase's first adjective. A
child a phrase was generated with, such as its article, is addressed the same way,
as (('np', 1), ('det', 0)). There is one address language, and it knows nothing of
how constituents are arranged: it only resolves, replaces, and relates addresses.
"""
from dataclasses import replace

from .DialogState import Constituent


class ConstituentAddresses:
    """
    `ConstituentAddresses` is a category whose objects are addresses and whose arrows
    relate an address to its parent, its last label, and its children, and resolve or
    replace what an address addresses within a statement. It is built from
    `Constituents`, which labels each constituent's children.
    """
    ROOT = ()

    def __init__(self, constituents):
        self.constituents = constituents

    def child(self, address, label):
        return (*address, label)

    def parent(self, address):
        return address[:-1]

    def label(self, address):
        """The last label of the address: what its parent calls it."""
        return address[-1]

    def resolve(self, statement, address):
        """The constituent or generated child at this address, else None."""
        node = statement
        for label in address:
            if not isinstance(node, Constituent):
                return None
            node = self.constituents.children(node).get(label)
        return node

    def replace(self, statement, address, replacement):
        """The statement with the added constituent at this address replaced by `replacement`."""
        if address == self.ROOT:
            return replacement
        index = self.constituents.labels(statement)[1].index(address[0])
        child = self.replace(statement.added[index], address[1:], replacement)
        return replace(statement, added=(*statement.added[:index], child, *statement.added[index + 1:]))

    def all(self, statement):
        """The address of every child under the statement, each before those of its children."""
        result = []
        def visit(constituent, address):
            children = self.constituents.children(constituent)
            for label in constituent.arrangement:
                result.append(self.child(address, label))
                if isinstance(children[label], Constituent):
                    visit(children[label], self.child(address, label))
        visit(statement, self.ROOT)
        return tuple(result)

    def is_ancestor(self, ancestor, descendant):
        return len(descendant) > len(ancestor) and descendant[:len(ancestor)] == ancestor
