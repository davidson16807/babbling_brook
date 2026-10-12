"""`ConstituentAddressOperations` translates what the player does to the constituent at an
address into a new root. Each operation takes the root, usually the statement, and returns
the whole root; nothing else in the dialog changes a constituent.

It owns the rules of arrangement: an arrangement changes only as the player changes it. When
a constituent is reinflected, children the new inflection keeps, and every added child, stay
where the player put them; children it lacks are dropped, and one it adds is inserted where
the language put it, counting from the front, so "the red ball" becomes "to the red ball".
When generated children come and go, or an added child is withdrawn, the labels of added
children are renumbered (see ConstituentAddresses.py), and `renamed` says how.
"""
from dataclasses import replace

from .DialogState import Constituent


class ConstituentAddressOperations:
    def __init__(self, addresses):
        self.addresses = addresses

    def _labels(self, addresses):
        return tuple(self.addresses.label(address) for address in addresses)

    def _arranged(self, root, address, arrangement):
        constituent = self.addresses.resolve(root, address)
        return self.addresses.replace(root, address, replace(constituent, arrangement=tuple(arrangement)))

    def constituent(self, rule):
        """A new constituent of `rule`, its children in the order the language generated them."""
        new = Constituent(rule)
        return replace(new, arrangement=self._labels(self.addresses.generated(new, self.addresses.ROOT)))

    def reinflect(self, root, address, inflection):
        """The root with the constituent at this address given the `Rule` `inflection`."""
        old_added = self._labels(self.addresses.added(root, address))
        constituent = self.addresses.resolve(root, address)
        root = self.addresses.replace(root, address, replace(constituent, inflection=inflection))
        generated = self._labels(self.addresses.generated(root, address))
        renamed = dict(zip(old_added, self._labels(self.addresses.added(root, address))))
        arrangement = [renamed.get(label, label) for label in constituent.arrangement
                       if label in renamed or label in generated]
        for index, label in enumerate(generated):
            if label not in arrangement:
                arrangement.insert(min(index, len(arrangement)), label)
        return self._arranged(root, address, arrangement)

    def adopt(self, root, parent, child, index):
        """The root with `child`, a `Constituent` or a `Rule`, added to the constituent at address
        `parent` at `index` of its arrangement: (root, the child's address). Adopting renumbers
        no other label, since the child is counted last among its part of speech."""
        child = child if isinstance(child, Constituent) else self.constituent(child)
        constituent = self.addresses.resolve(root, parent)
        root = self.addresses.replace(root, parent, replace(constituent, added=(*constituent.added, child)))
        address = self.addresses.added(root, parent)[-1]
        arrangement = list(constituent.arrangement)
        arrangement.insert(max(0, min(index, len(arrangement))), self.addresses.label(address))
        return self._arranged(root, parent, arrangement), address

    def withdraw(self, root, address):
        """The root without the added constituent at this address: (root, the constituent, renamed),
        where `renamed` maps the old label of each later sibling of its part of speech to its new one."""
        parent, label = self.addresses.parent(address), self.addresses.label(address)
        old_added = self._labels(self.addresses.added(root, parent))
        index = old_added.index(label)
        constituent = self.addresses.resolve(root, parent)
        withdrawn = constituent.added[index]
        root = self.addresses.replace(root, parent, replace(
            constituent, added=(*constituent.added[:index], *constituent.added[index + 1:])))
        renamed = {old: new for old, new in zip((*old_added[:index], *old_added[index + 1:]),
                                                self._labels(self.addresses.added(root, parent))) if old != new}
        arrangement = [renamed.get(other, other) for other in constituent.arrangement if other != label]
        return self._arranged(root, parent, arrangement), withdrawn, renamed

    def move(self, root, address, index):
        """The root with the child at this address at `index` of its parent's arrangement, counted without it."""
        parent, label = self.addresses.parent(address), self.addresses.label(address)
        arrangement = [other for other in self.addresses.resolve(root, parent).arrangement if other != label]
        arrangement.insert(max(0, min(index, len(arrangement))), label)
        return self._arranged(root, parent, arrangement)

    def readdress(self, address, withdrawn, renamed):
        """`address` after the constituent at `withdrawn` was withdrawn and its siblings `renamed`:
        None if it addressed the withdrawn constituent or anything within it."""
        parent = self.addresses.parent(withdrawn)
        if not self.addresses.is_ancestor(parent, address):
            return address
        below = address[len(parent)]
        if below == self.addresses.label(withdrawn):
            return None
        return (*parent, renamed.get(below, below), *address[len(parent) + 1:])
