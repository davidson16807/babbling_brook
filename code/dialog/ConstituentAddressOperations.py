"""Translates address-addressed operations on the statement into the address-free arrows
of `Constituents`.

It owns resolving an address's parent, replacing along an address, and readdressing an
address after labels are renumbered; it owns no rules of arrangement. Each operation
takes the whole statement and returns the whole statement.
"""


class ConstituentAddressOperations:
    """
    `ConstituentAddressOperations` is a category whose objects are statements and whose
    arrows reinflect, adopt, withdraw, move, or hide the constituent at an address. It is
    built from `ConstituentAddresses` and `Constituents`.
    """
    def __init__(self, addresses, constituents):
        self.addresses = addresses
        self.constituents = constituents

    def _parent(self, statement, address):
        return self.addresses.resolve(statement, self.addresses.parent(address))

    def _with_parent(self, statement, address, parent):
        return self.addresses.replace(statement, self.addresses.parent(address), parent)

    def reinflect(self, statement, address, inflection):
        """The statement with the constituent at this address given the `Rule` tree `inflection`."""
        constituent = self.constituents.reinflected(self.addresses.resolve(statement, address), inflection)
        return self.addresses.replace(statement, address, constituent)

    def adopt(self, statement, parent, child, index):
        """The statement with `child` added at `index` of the constituent at address `parent`:
        (statement, the child's address). Adopting renumbers no other label."""
        constituent, label = self.constituents.adopted(self.addresses.resolve(statement, parent), child, index)
        return self.addresses.replace(statement, parent, constituent), self.addresses.child(parent, label)

    def withdraw(self, statement, address):
        """The statement without the added constituent at this address: (statement, the
        constituent, renamed), where `renamed` maps each label its siblings had to the one they have now."""
        parent, child, renamed = self.constituents.withdrawn(self._parent(statement, address),
                                                             self.addresses.label(address))
        return self._with_parent(statement, address, parent), child, renamed

    def move(self, statement, address, index):
        """The statement with the child at this address at `index` of its parent's arrangement, counted without it."""
        parent = self.constituents.moved(self._parent(statement, address), self.addresses.label(address), index)
        return self._with_parent(statement, address, parent)

    def hide(self, statement, address):
        """The statement as shown while the child at this address is dragged out of its parent."""
        parent = self.constituents.hidden(self._parent(statement, address), self.addresses.label(address))
        return self._with_parent(statement, address, parent)

    def readdress(self, address, withdrawn, renamed):
        """`address` after the constituent at `withdrawn` was withdrawn and its siblings renamed
        by `renamed`: None if it addressed the withdrawn constituent or something within it."""
        parent = self.addresses.parent(withdrawn)
        if not self.addresses.is_ancestor(parent, address):
            return address
        below = address[len(parent)]
        if below == self.addresses.label(withdrawn):
            return None
        return (*parent, renamed.get(below, below), *address[len(parent) + 1:])
