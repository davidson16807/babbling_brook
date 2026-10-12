"""Arrows on one noun phrase, and the reading of `Rule` trees they need.

Inflections are the languages repo's `Rule` trees: each `Rule` has its part of speech
as `tag`, the tags it was inflected with as `tags`, and flat `content` of words and
the `Rule`s of the parts of speech within it. Only `tag` and `content` are read here,
so this module does not import the repo.

A noun phrase is a `Word` whose inflection is an 'np' `Rule`. Its children are the
children of that `Rule` that read as something (its adposition, article, noun, ...),
which the language generates, followed by the children the player added (adjectives,
and determiners such as "this"). A label addresses each child as the `index`th child
of its part of speech, counting generated children first, so `('det', 0)` is "the" in
"the ball". The phrase's `arrangement` is every child's label, in the player's order;
nothing here reorders it. When generated children come and go, as when the phrase is
reinflected, the labels of added children are renumbered to match. Labels are internal
to the dialog: what leaves it is a `Rule` tree, from `ordered`.
"""
from dataclasses import replace


class NounPhrases:
    """
    `NounPhrases` is a category whose objects are noun phrases and whose arrows
    reinflect a phrase, add a child to it, withdraw one, move one, and read the
    phrase as text or as a `Rule` tree in the player's order.
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

    def generated(self, phrase) -> list:
        """(part of speech, child) for each child of the phrase's inflection that reads as something."""
        rule = phrase.inflection
        parts = [(rule.tag if child is None or isinstance(child, str) else child.tag, child) for child in rule.content]
        return [(part, child) for part, child in parts if self.words(child, part)]

    def labels(self, phrase) -> tuple[tuple, tuple]:
        """(the labels of the generated children, the labels of the added children), in their orders."""
        counts = {}
        def label(part):
            counts[part] = counts.get(part, 0) + 1
            return (part, counts[part] - 1)
        generated = tuple(label(part) for part, _ in self.generated(phrase))
        return generated, tuple(label(rule.tag) for _, rule in phrase.added)

    def children(self, phrase) -> dict:
        """Each label of the phrase → its child."""
        generated, added = self.labels(phrase)
        return {**dict(zip(generated, (child for _, child in self.generated(phrase)))),
                **dict(zip(added, (rule for _, rule in phrase.added)))}

    def texts(self, phrase) -> dict:
        """Each label of the phrase → what its child reads as."""
        return {label: self.text(child) for label, child in self.children(phrase).items()}

    def items(self, phrase) -> list:
        """(label, text) for each child of the phrase, in the player's order."""
        texts = self.texts(phrase)
        return [(label, texts[label]) for label in phrase.arrangement]

    def is_added(self, phrase, label) -> bool:
        return label in self.labels(phrase)[1]

    def addition(self, phrase, label) -> tuple:
        """(lexeme, `Rule`) of the added child with this label."""
        return phrase.added[self.labels(phrase)[1].index(label)]

    def arranged(self, phrase):
        """A newly placed phrase, its generated children in the order the language produced them."""
        return replace(phrase, arrangement=self.labels(phrase)[0])

    def reinflected(self, phrase, inflection):
        """The phrase with the `Rule` tree `inflection`.

        Children the inflection keeps, and every added child, stay where the player
        put them; children it lacks are dropped. A child it adds is inserted where the
        language put it, counting from the front of the phrase.
        """
        _, old_added = self.labels(phrase)
        new = replace(phrase, inflection=inflection)
        generated, added = self.labels(new)
        renamed = dict(zip(old_added, added))
        result = [renamed.get(label, label) for label in phrase.arrangement if label in renamed or label in generated]
        for index, label in enumerate(generated):
            if label not in result:
                result.insert(min(index, len(result)), label)
        return replace(new, arrangement=tuple(result))

    def reinflected_child(self, phrase, label, inflection):
        """The phrase with the added child of this label given the `Rule` tree `inflection`."""
        index = self.labels(phrase)[1].index(label)
        lexeme, _ = phrase.added[index]
        return replace(phrase, added=(*phrase.added[:index], (lexeme, inflection), *phrase.added[index + 1:]))

    def adopted(self, phrase, lexeme, inflection, index):
        """The phrase with a child added at `index` of its arrangement: (phrase, the child's label)."""
        phrase = replace(phrase, added=(*phrase.added, (lexeme, inflection)))
        label = self.labels(phrase)[1][-1]  # counted last among its part, so no other label changes
        arrangement = list(phrase.arrangement)
        arrangement.insert(max(0, min(index, len(arrangement))), label)
        return replace(phrase, arrangement=tuple(arrangement)), label

    def withdrawn(self, phrase, label):
        """The phrase without the added child of this label: (phrase, (lexeme, `Rule`) of the child)."""
        _, added = self.labels(phrase)
        index = added.index(label)
        rest = replace(phrase, added=(*phrase.added[:index], *phrase.added[index + 1:]))
        renamed = dict(zip((*added[:index], *added[index + 1:]), self.labels(rest)[1]))
        arrangement = tuple(renamed.get(other, other) for other in phrase.arrangement if other != label)
        return replace(rest, arrangement=arrangement), phrase.added[index]

    def hidden(self, phrase, label):
        """The phrase as shown while the child of this label is dragged out of it."""
        return replace(phrase, arrangement=tuple(other for other in phrase.arrangement if other != label))

    def moved(self, phrase, label, index):
        """The phrase with the child of this label at `index` of its arrangement, counted without it."""
        arrangement = list(self.hidden(phrase, label).arrangement)
        arrangement.insert(max(0, min(index, len(arrangement))), label)
        return replace(phrase, arrangement=tuple(arrangement))

    def ordered(self, phrase):
        """The phrase's `Rule` with its children, generated and added, in the player's order."""
        rule, children = phrase.inflection, self.children(phrase)
        return type(rule)(rule.tag, rule.tags, [children[label] for label in phrase.arrangement])
