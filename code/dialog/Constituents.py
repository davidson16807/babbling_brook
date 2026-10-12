"""Arrows on constituents: the statement, the phrases placed in it, and the words added to those.

Inflections are the languages repo's `Rule` trees: each `Rule` has its part of speech
as `tag`, the tags it was inflected with as `tags`, and flat `content` of words and
the `Rule`s of the parts of speech within it. Only `tag` and `content` are read here,
so this module does not import the repo.

A `Constituent` (see DialogState.py) is a `Rule` as the language generated it, the
constituents the player added to it, and an arrangement. Its children are the
children of its `Rule` that read as something (a noun phrase's adposition, article,
noun, ...), followed by the constituents added to it (the statement's phrases, a noun
phrase's adjectives, and later determiners such as "this"). A label addresses each
child as the `index`th child of its part of speech, counting generated children first
and added ones in their order of addition, so ('det', 0) is "the" in "the ball". An
arrangement is a tuple of labels: a constituent's arrangement is every child's label,
in the player's order, and nothing here reorders it. When generated children come and
go, as when a constituent is reinflected, or an added child is withdrawn, the labels
of added children are renumbered to match. Labels and arrangements are internal to
the dialog: what leaves it is a `Rule` tree, from `ordered`. Nothing here takes an
address; ConstituentAddresses.py addresses constituents, and
ConstituentAddressOperations.py translates address-addressed operations into these.
"""
from dataclasses import replace

from .DialogState import Constituent


class Constituents:
    """
    `Constituents` is a category whose objects are constituents and whose arrows read a
    constituent as text or as a `Rule` tree in the player's order, and reinflect one,
    add a child to it, withdraw one, or move one.
    """
    def words(self, node, part='') -> tuple[tuple[str, str], ...]:
        """Each word of a `Rule` tree, in order, as (the part of speech it is in, its text).

        '∅' marks a linguistic zero, so words that read as nothing are left out.
        A missing inflection is indicated by `None` and reads as '[MISSING]'.
        """
        if node is None:
            return ((part, '[MISSING]'),)
        if isinstance(node, str):
            text = ' '.join(node.replace('∅', '').split())
            return ((part, text),) if text else ()
        return tuple(word for child in node.content for word in self.words(child, node.tag))

    def tokens(self, constituent) -> tuple[str, ...]:
        """The words of a constituent, in the player's order."""
        children, result = self.children(constituent), []
        for label in constituent.arrangement:
            child = children[label]
            result += (self.tokens(child) if isinstance(child, Constituent)
                       else [text for _, text in self.words(child, label[0])])
        return tuple(result)

    def text(self, node) -> str:
        """What a constituent or a `Rule` tree reads as."""
        if isinstance(node, Constituent):
            return ' '.join(self.tokens(node))
        return ' '.join(text for _, text in self.words(node))

    def index(self, options, inflection) -> int:
        """The index of the option among `options` that reads as `inflection`, word for word."""
        return [self.words(option) for option in options].index(self.words(inflection))

    def generated(self, constituent) -> list:
        """(part of speech, child) for each child of the constituent's `Rule` that reads as something."""
        rule = constituent.inflection
        parts = [(rule.tag if child is None or isinstance(child, str) else child.tag, child) for child in rule.content]
        return [(part, child) for part, child in parts if self.words(child, part)]

    def labels(self, constituent) -> tuple[tuple, tuple]:
        """(the labels of the generated children, the labels of the added children), in their orders."""
        counts = {}
        def label(part):
            counts[part] = counts.get(part, 0) + 1
            return (part, counts[part] - 1)
        generated = tuple(label(part) for part, _ in self.generated(constituent))
        return generated, tuple(label(child.inflection.tag) for child in constituent.added)

    def children(self, constituent) -> dict:
        """Each label of the constituent → its child: a `Rule` it was generated with, or a `Constituent` added to it."""
        generated, added = self.labels(constituent)
        return {**dict(zip(generated, (child for _, child in self.generated(constituent)))),
                **dict(zip(added, constituent.added))}

    def is_added(self, constituent, label) -> bool:
        return label in self.labels(constituent)[1]

    def arranged(self, inflection):
        """A new constituent of the `Rule` tree `inflection`, its children in the order the language produced them."""
        constituent = Constituent(inflection)
        return replace(constituent, arrangement=self.labels(constituent)[0])

    def reinflected(self, constituent, inflection):
        """The constituent with the `Rule` tree `inflection`.

        Children the inflection keeps, and every added child, stay where the player
        put them; children it lacks are dropped. A child it adds is inserted where the
        language put it, counting from the front.
        """
        _, old_added = self.labels(constituent)
        new = replace(constituent, inflection=inflection)
        generated, added = self.labels(new)
        renamed = dict(zip(old_added, added))
        result = [renamed.get(label, label) for label in constituent.arrangement
                  if label in renamed or label in generated]
        for index, label in enumerate(generated):
            if label not in result:
                result.insert(min(index, len(result)), label)
        return replace(new, arrangement=tuple(result))

    def adopted(self, constituent, child, index):
        """The constituent with `child` added at `index` of its arrangement: (constituent, the child's label)."""
        constituent = replace(constituent, added=(*constituent.added, child))
        label = self.labels(constituent)[1][-1]  # counted last among its part, so no other label changes
        arrangement = list(constituent.arrangement)
        arrangement.insert(max(0, min(index, len(arrangement))), label)
        return replace(constituent, arrangement=tuple(arrangement)), label

    def withdrawn(self, constituent, label):
        """The constituent without the added child of this label: (constituent, the child, renamed),
        where `renamed` maps the label of each other added child to its label now."""
        _, added = self.labels(constituent)
        index = added.index(label)
        rest = replace(constituent, added=(*constituent.added[:index], *constituent.added[index + 1:]))
        renamed = dict(zip((*added[:index], *added[index + 1:]), self.labels(rest)[1]))
        arrangement = tuple(renamed.get(other, other) for other in constituent.arrangement if other != label)
        return replace(rest, arrangement=arrangement), constituent.added[index], renamed

    def hidden(self, constituent, label):
        """The constituent as shown while its child of this label is dragged out of it."""
        return replace(constituent, arrangement=tuple(other for other in constituent.arrangement if other != label))

    def moved(self, constituent, label, index):
        """The constituent with its child of this label at `index` of its arrangement, counted without it."""
        arrangement = list(self.hidden(constituent, label).arrangement)
        arrangement.insert(max(0, min(index, len(arrangement))), label)
        return replace(constituent, arrangement=tuple(arrangement))

    def ordered(self, constituent):
        """The constituent's `Rule` with its children, generated and added, in the player's order."""
        rule, children = constituent.inflection, self.children(constituent)
        return type(rule)(rule.tag, rule.tags, [self.ordered(child) if isinstance(child, Constituent) else child
                                                for child in (children[label] for label in constituent.arrangement)])
