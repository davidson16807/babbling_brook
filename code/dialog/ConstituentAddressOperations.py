"""Operations on constituents by address: reading them, building them, and rearranging them.

A constituent (see DialogState.py) is a `Rule` as the language generated it, the
constituents the player added to it, and its arrangement: every child's label, in the
player's order (see ConstituentAddresses.py for labels). Nothing here reorders an
arrangement on its own; each operation does exactly what the player did. When generated
children come and go, as when a constituent is reinflected, or an added child is
withdrawn, the labels of added children are renumbered to match. Labels, arrangements,
and addresses are internal to the dialog: what leaves it is a `Rule` tree, from `ordered`.

Each operation takes a root, usually the whole statement, and an address within it, and
what it changes it returns as the whole root. Only `tag` and `content` of a `Rule` are
read, so this module does not import the languages repo.
"""
from dataclasses import replace

from .DialogState import Constituent


class ConstituentAddressOperations:
    """
    `ConstituentAddressOperations` is a category whose objects are statements and whose
    arrows read the constituent at an address as words, text, or a `Rule` tree in the
    player's order, and reinflect, adopt, withdraw, move, or hide it. It is built from
    `ConstituentAddresses`.
    """
    def __init__(self, addresses):
        self.addresses = addresses

    def _added_labels(self, root, address):
        """The labels of the children added to the constituent at this address, in their order of addition."""
        return tuple(self.addresses.label(child) for child in self.addresses.children(root, address)
                     if isinstance(self.addresses.resolve(root, child), Constituent))

    def _generated_labels(self, root, address):
        return tuple(self.addresses.label(child) for child in self.addresses.children(root, address)
                     if not isinstance(self.addresses.resolve(root, child), Constituent))

    def _arranged_as(self, root, address, arrangement):
        constituent = self.addresses.resolve(root, address)
        return self.addresses.replace(root, address, replace(constituent, arrangement=tuple(arrangement)))

    def words(self, root, address=()) -> tuple[tuple[str, str], ...]:
        """Each word at this address, in the player's order, as (the part of speech it is in, its text).

        `root` may also be a `Rule` tree on its own. '∅' marks a linguistic zero, so words that
        read as nothing are left out; a missing inflection is indicated by `None` and reads as '[MISSING]'.
        """
        node = self.addresses.resolve(root, address)
        if not isinstance(node, Constituent):
            # A child a phrase was generated with, or a `Rule` tree on its own.
            return self._read(node, self.addresses.label(address)[0] if address else '')
        # Each child is read from the constituent itself, rather than resolved again from the root.
        return tuple(word for label in node.arrangement for word in self.words(node, (label,)))

    def _read(self, node, part):
        if node is None:
            return ((part, '[MISSING]'),)
        if isinstance(node, str):
            text = ' '.join(node.replace('∅', '').split())
            return ((part, text),) if text else ()
        return tuple(word for child in node.content for word in self._read(child, node.tag))

    def text(self, root, address=()) -> str:
        """What the constituent, generated child, or `Rule` tree at this address reads as."""
        return ' '.join(text for _, text in self.words(root, address))

    def arranged(self, inflection):
        """A new constituent of the `Rule` tree `inflection`, its children in the order the language produced them."""
        constituent = Constituent(inflection)
        return replace(constituent, arrangement=self._generated_labels(constituent, self.addresses.ROOT))

    def reinflect(self, root, address, inflection):
        """The root with the constituent at this address given the `Rule` tree `inflection`.

        Children the inflection keeps, and every added child, stay where the player put
        them; children it lacks are dropped. A child it adds is inserted where the language
        put it, counting from the front.
        """
        old_added = self._added_labels(root, address)
        constituent = replace(self.addresses.resolve(root, address), inflection=inflection)
        root = self.addresses.replace(root, address, constituent)
        generated, added = self._generated_labels(root, address), self._added_labels(root, address)
        renamed = dict(zip(old_added, added))
        result = [renamed.get(label, label) for label in constituent.arrangement
                  if label in renamed or label in generated]
        for index, label in enumerate(generated):
            if label not in result:
                result.insert(min(index, len(result)), label)
        return self._arranged_as(root, address, result)

    def adopt(self, root, parent, child, index):
        """The root with `child` added at `index` of the arrangement of the constituent at address
        `parent`: (root, the child's address). Adopting renumbers no other label."""
        constituent = self.addresses.resolve(root, parent)
        root = self.addresses.replace(root, parent, replace(constituent, added=(*constituent.added, child)))
        label = self._added_labels(root, parent)[-1]  # counted last among its part
        arrangement = list(constituent.arrangement)
        arrangement.insert(max(0, min(index, len(arrangement))), label)
        return self._arranged_as(root, parent, arrangement), self.addresses.child(parent, label)

    def withdraw(self, root, address):
        """The root without the added constituent at this address: (root, the constituent, renamed),
        where `renamed` maps each label its siblings had to the one they have now."""
        parent, label = self.addresses.parent(address), self.addresses.label(address)
        added = self._added_labels(root, parent)
        index = added.index(label)
        constituent = self.addresses.resolve(root, parent)
        withdrawn = constituent.added[index]
        root = self.addresses.replace(root, parent, replace(
            constituent, added=(*constituent.added[:index], *constituent.added[index + 1:])))
        renamed = dict(zip((*added[:index], *added[index + 1:]), self._added_labels(root, parent)))
        arrangement = [renamed.get(other, other) for other in constituent.arrangement if other != label]
        return self._arranged_as(root, parent, arrangement), withdrawn, renamed

    def hide(self, root, address):
        """The root as shown while the child at this address is dragged out of its parent."""
        parent, label = self.addresses.parent(address), self.addresses.label(address)
        arrangement = self.addresses.resolve(root, parent).arrangement
        return self._arranged_as(root, parent, [other for other in arrangement if other != label])

    def move(self, root, address, index):
        """The root with the child at this address at `index` of its parent's arrangement, counted without it."""
        parent, label = self.addresses.parent(address), self.addresses.label(address)
        arrangement = [other for other in self.addresses.resolve(root, parent).arrangement if other != label]
        arrangement.insert(max(0, min(index, len(arrangement))), label)
        return self._arranged_as(root, parent, arrangement)

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

    def ordered(self, root, address=()):
        """The `Rule` of the constituent at this address, its children, generated and added, in the player's order."""
        constituent = self.addresses.resolve(root, address)
        rule = constituent.inflection
        children = [self.addresses.resolve(root, self.addresses.child(address, label)) for label in constituent.arrangement]
        return type(rule)(rule.tag, rule.tags, [
            self.ordered(child) if isinstance(child, Constituent) else child for child in children])
