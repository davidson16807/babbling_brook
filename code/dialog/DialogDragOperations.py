"""`DialogDragOperations.choices` is the single entry point for drag behavior: what a drop
of a source on a target makes of the statement.

A source is the address of what is dragged, either a placed constituent or a child a
phrase was generated with, or a new `Constituent` dragged from the inventory. A target
is a `PlaceDrop` or a `RemoveDrop`. `choices` returns every statement the drop can
produce, as `DragChoice`s; a drop that is not allowed returns none. `targets` and
`removable` say which drops are allowed, so the layout only maps the pointer to them.
"""
from dataclasses import dataclass, field

from .DialogState import Constituent

# The parts of speech a constituent may have added to it, by its own part of speech.
ACCEPTS = {'clause': {'np', 'vp'}, 'np': {'adj'}}


@dataclass(frozen=True)
class PlaceDrop:
    parent: tuple    # address of the constituent it would become a child of; () for the statement
    index: int       # in that constituent's arrangement, not counting the dragged item

@dataclass(frozen=True)
class RemoveDrop:
    pass


@dataclass(frozen=True)
class DragChoice:
    statement: object                  # the statement the drop makes
    address: tuple | None              # of what was dragged, now; None if it was removed
    withdrawn: tuple | None = None     # the address it was withdrawn from, if it was
    renamed: dict = field(default_factory=dict)  # each label its old siblings had → the one they have now


class DialogDragOperations:
    """
    `DialogDragOperations` is a category whose objects are statements and whose arrows
    map a drag's source and target to the statements it can produce. It is built from
    `ConstituentAddresses`, `ConstituentAddressOperations`, and `Constituents`.
    """
    def __init__(self, addresses, address_operations, constituents):
        self.addresses = addresses
        self.address_operations = address_operations
        self.constituents = constituents

    def _is_new(self, source):
        return isinstance(source, Constituent)

    def _generated(self, statement, source):
        """Whether the source is a child a phrase was generated with, such as its article."""
        return not self._is_new(source) and not isinstance(self.addresses.resolve(statement, source), Constituent)

    def _tag(self, statement, source):
        node = source if self._is_new(source) else self.addresses.resolve(statement, source)
        return node.inflection.tag

    def targets(self, statement, source) -> tuple:
        """The addresses of the constituents the source may be placed in."""
        if self._generated(statement, source):
            # Children a phrase was generated with stay in it.
            return (self.addresses.parent(source),)
        tag = self._tag(statement, source)
        candidates = (self.addresses.ROOT, *self.addresses.all(statement))
        return tuple(address for address in candidates
                     if isinstance(node := self.addresses.resolve(statement, address), Constituent)
                     and tag in ACCEPTS.get(node.inflection.tag, ()))

    def removable(self, statement, source) -> bool:
        """Whether dropping the source on the inventory removes it: whatever the player added can go."""
        return not self._is_new(source) and not self._generated(statement, source)

    def choices(self, statement, source, target) -> tuple:
        if isinstance(target, RemoveDrop):
            if not self.removable(statement, source):
                return ()
            statement, _, renamed = self.address_operations.withdraw(statement, source)
            return (DragChoice(statement, None, source, renamed),)
        if not isinstance(target, PlaceDrop) or target.parent not in self.targets(statement, source):
            return ()
        if self._is_new(source):
            statement, address = self.address_operations.adopt(statement, target.parent, source, target.index)
            return (DragChoice(statement, address),)
        if target.parent == self.addresses.parent(source):
            statement = self.address_operations.move(statement, source, target.index)
            return (DragChoice(statement, source),)
        # Adopting renumbers nothing, so the source's address still holds for withdrawing it.
        child = self.addresses.resolve(statement, source)
        statement, address = self.address_operations.adopt(statement, target.parent, child, target.index)
        statement, _, renamed = self.address_operations.withdraw(statement, source)
        return (DragChoice(statement, self.address_operations.readdress(address, source, renamed), source, renamed),)
