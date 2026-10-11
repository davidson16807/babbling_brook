"""Arrows on the arrangement of one noun phrase.

A noun phrase's `arrangement` is its words in the player's order: a `Slot` for each
word of its inflection's list tree (article, adposition, noun, ...) and a `Word` for
each adjective. The player orders all of them; nothing here reorders them.
"""
from .DialogState import Slot, Word


class Arrangements:
    """
    `Arrangements` is a category whose objects are noun-phrase arrangements and whose
    arrows place an item, remove one, fit an arrangement to another inflection, and
    read an arrangement as text. It is built from `ListTrees`, which reads the list
    tree of the phrase's inflection.
    """
    def __init__(self, list_trees):
        self.list_trees = list_trees

    def is_phrase(self, tree) -> bool:
        return self.list_trees.kind(tree) == 'np'

    def is_adjective(self, tree) -> bool:
        return self.list_trees.kind(tree) == 'adj'

    def slots(self, tree) -> tuple[Slot, ...]:
        """A slot per word of the list tree, in the order the language produced them."""
        counts, result = {}, []
        for part, _ in self.list_trees.words(tree):
            result.append(Slot(part, counts.get(part, 0)))
            counts[part] = counts.get(part, 0) + 1
        return tuple(result)

    def texts(self, tree) -> dict[Slot, str]:
        """Each slot of the list tree → the text of its word."""
        return dict(zip(self.slots(tree), (text for _, text in self.list_trees.words(tree))))

    def arrange(self, arrangement, tree) -> tuple:
        """`arrangement` after the phrase takes the inflection `tree`.

        Slots the inflection keeps, and every adjective, stay where the player put
        them; slots it lacks are dropped. A slot it adds is inserted where the
        language put that word, counting from the front of the phrase.
        """
        wanted = self.slots(tree)
        result = [item for item in arrangement if isinstance(item, Word) or item in wanted]
        for index, slot in enumerate(wanted):
            if slot not in result:
                result.insert(min(index, len(result)), slot)
        return tuple(result)

    def items(self, arrangement, tree) -> list[tuple[object, str]]:
        """(slot or adjective, text) for each item of `arrangement`, read with `tree`."""
        slot_texts = self.texts(tree)
        return [(item, slot_texts[item] if isinstance(item, Slot) else self.list_trees.text(item.inflection))
                for item in arrangement]

    def remove(self, arrangement, item) -> tuple:
        if isinstance(item, Slot):
            return tuple(other for other in arrangement if other != item)
        return tuple(other for other in arrangement if not (isinstance(other, Word) and other.id == item.id))

    def insert(self, arrangement, item, index: int) -> tuple:
        """`item` at `index` of `arrangement`, counted without `item`."""
        result = list(self.remove(arrangement, item))
        result.insert(max(0, min(index, len(result))), item)
        return tuple(result)
