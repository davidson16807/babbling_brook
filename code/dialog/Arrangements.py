"""Arrows on the arrangement of one noun phrase, and the reading of `Rule` trees they need.

Inflections are the languages repo's `Rule` trees: each `Rule` has its part of speech
as `tag`, the tags it was inflected with as `tags`, and flat `content` of words and
the `Rule`s of the parts of speech within it. Only `tag` and `content` are read here,
so this module does not import the repo.

A noun phrase's `arrangement` is its items in the player's order: a `Slot` for each
child of the phrase's `Rule` that reads as something (its adposition, article, noun,
...) and a `Word` for each adjective. The player orders all of them; nothing here
reorders them. Slots exist only inside the dialog: what leaves it is a `Rule` tree.
"""
from .DialogState import Slot, Word


class Arrangements:
    """
    `Arrangements` is a category whose objects are noun-phrase arrangements and whose
    arrows place an item, remove one, fit an arrangement to another inflection, and
    read an arrangement as text or as a `Rule` tree in the player's order.
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

    def text(self, node) -> str:
        return ' '.join(text for _, text in self.words(node))

    def children(self, rule) -> dict:
        """Each slot of a noun phrase's `Rule` → its child: the `index`th child of its part.

        Children that read as nothing, such as an adposition '∅', have no slot.
        """
        counts, result = {}, {}
        for child in rule.content:
            part = rule.tag if child is None or isinstance(child, str) else child.tag
            if self.words(child, part):
                result[Slot(part, counts.get(part, 0))] = child
                counts[part] = counts.get(part, 0) + 1
        return result

    def slots(self, rule) -> tuple[Slot, ...]:
        """A slot per child of the `Rule` that reads as something, in the order the language produced them."""
        return tuple(self.children(rule))

    def texts(self, rule) -> dict[Slot, str]:
        """Each slot of the `Rule` → what its child reads as."""
        return {slot: self.text(child) for slot, child in self.children(rule).items()}

    def arrange(self, arrangement, rule) -> tuple:
        """`arrangement` after the phrase takes the inflection `rule`.

        Slots the inflection keeps, and every adjective, stay where the player put
        them; slots it lacks are dropped. A slot it adds is inserted where the
        language put that child, counting from the front of the phrase.
        """
        wanted = self.slots(rule)
        result = [item for item in arrangement if isinstance(item, Word) or item in wanted]
        for index, slot in enumerate(wanted):
            if slot not in result:
                result.insert(min(index, len(result)), slot)
        return tuple(result)

    def items(self, arrangement, rule) -> list[tuple[object, str]]:
        """(slot or adjective, text) for each item of `arrangement`, read with `rule`."""
        slot_texts = self.texts(rule)
        return [(item, slot_texts[item] if isinstance(item, Slot) else self.text(item.inflection))
                for item in arrangement]

    def ordered(self, arrangement, rule):
        """The noun phrase's `Rule` with its children and adjectives in the order of `arrangement`."""
        children = self.children(rule)
        return type(rule)(rule.tag, rule.tags, [children[item] if isinstance(item, Slot) else item.inflection
                                                for item in arrangement])

    def remove(self, arrangement, item) -> tuple:
        if isinstance(item, Slot):
            return tuple(other for other in arrangement if other != item)
        return tuple(other for other in arrangement if not (isinstance(other, Word) and other.id == item.id))

    def insert(self, arrangement, item, index: int) -> tuple:
        """`item` at `index` of `arrangement`, counted without `item`."""
        result = list(self.remove(arrangement, item))
        result.insert(max(0, min(index, len(result))), item)
        return tuple(result)
