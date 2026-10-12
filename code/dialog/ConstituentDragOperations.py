"""`ConstituentDragOperations.drop` is the single entry point for drag behavior: what a drop of
a source on a target makes of the statement.

A source is the address of what is dragged, a placed constituent or a child a phrase was
generated with, or a `Rule` dragged from the inventory. A target is a `PlaceDrop`, into a
constituent at an index of its arrangement, or a `RemoveDrop`, onto the inventory. A drop has
one result, or none if it is not allowed. `targets` and `removable` say beforehand which drops
are allowed, as xcraft's `moves_for_source` does.

What may go where:
    * a child a phrase was generated with, such as its article, moves only within that phrase;
    * anything the player added may be placed in any constituent whose part of speech accepts
      its own (`ACCEPTS`), or removed;
    * a `Rule` from the inventory may be placed wherever its part of speech is accepted.
"""
from dataclasses import dataclass

from .DialogState import Constituent

# The parts of speech a constituent may have added to it, by its own part of speech.
ACCEPTS = {'clause': {'np', 'vp'}, 'np': {'adj'}}


@dataclass(frozen=True)
class PlaceDrop:
    parent: tuple    # address of the constituent the source would become a child of
    index: int       # in that constituent's arrangement, not counting the source

@dataclass(frozen=True)
class RemoveDrop:
    pass


class ConstituentDragOperations:
    def __init__(self, addresses, address_operations):
        self.addresses = addresses
        self.address_operations = address_operations

    def _placed(self, source):
        return isinstance(source, tuple)

    def _generated(self, statement, source):
        return self._placed(source) and not isinstance(self.addresses.resolve(statement, source), Constituent)

    def targets(self, statement, source) -> tuple:
        """The addresses of the constituents the source may be placed in."""
        if self._generated(statement, source):
            return (self.addresses.parent(source),)
        node = self.addresses.resolve(statement, source) if self._placed(source) else source
        tag = node.inflection.tag if isinstance(node, Constituent) else node.tag
        return tuple(address for address in (self.addresses.ROOT, *self.addresses.all(statement))
                     if isinstance(parent := self.addresses.resolve(statement, address), Constituent)
                     and tag in ACCEPTS.get(parent.inflection.tag, ()))

    def removable(self, statement, source) -> bool:
        """Whether the source may be removed: whatever the player added may be."""
        return self._placed(source) and not self._generated(statement, source)

    def drop(self, statement, source, target):
        """(statement, address, renamed): the statement after the drop, the source's address in it
        (None if it was removed), and the labels its withdrawal renumbered, old to new; None if the
        drop is not allowed."""
        if isinstance(target, RemoveDrop):
            if not self.removable(statement, source):
                return None
            statement, _, renamed = self.address_operations.withdraw(statement, source)
            return statement, None, renamed
        if not isinstance(target, PlaceDrop) or target.parent not in self.targets(statement, source):
            return None
        if not self._placed(source):
            statement, address = self.address_operations.adopt(statement, target.parent, source, target.index)
            return statement, address, {}
        if target.parent == self.addresses.parent(source):
            return self.address_operations.move(statement, source, target.index), source, {}
        # Adopting renumbers nothing, so the source's address still holds for withdrawing it.
        child = self.addresses.resolve(statement, source)
        statement, address = self.address_operations.adopt(statement, target.parent, child, target.index)
        statement, _, renamed = self.address_operations.withdraw(statement, source)
        return statement, self.address_operations.readdress(address, source, renamed), renamed
