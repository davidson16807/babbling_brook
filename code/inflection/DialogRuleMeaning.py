"""The meanings a speaker could assign to a statement: its readings that are grammatically consistent.

A statement is a `DialogRule` tree whose nodes each list the tags of every homonym
they could be. A reading is the same tree with one tagpoint chosen for each node,
so that every node's `tags` lists exactly one. `meaning` tries every reading and
keeps those that are grammatically self-consistent. It does not yet consider the
world the statement is said in.

Tagpoints are chosen per inflection the speaker chose, not per node: the words an
inflection came with, such as a noun phrase's article and noun, are read as the
same homonym as their phrase. Only the root, and what the speaker added to a node
(see `accepts`), are chosen independently, and a modifier only among the tagpoints
that agree with its noun phrase, since every meaning needs that agreement.

A reading is a meaning if its clause has exactly one verb phrase; no more than one
subject, which the verb agrees with; no two noun phrases in the same place (two
direct objects, say); every modifier agreeing with the noun phrase it modifies, in
the same place; and, unless the language's word order is free, its words in the
order the language would give that meaning. Whether a subject is required, or
forbidden, depends on the language and on `strict`:
    is_pro_drop             the subject may be left out
    is_pro_drop_imperative  the subject may be left out when the verb is imperative
    is_pro_drop_mandatory   where a subject may be left out, it must be
Each applies only when `strict`; otherwise a subject may always be left out or included.

Without `strict`, a statement with no meaning is read as if it had a single error.
Its meanings are then the readings that are meanings but for one of:
    the subject           its presence or absence, as above
    word order            the subject, verb, and objects are inflected correctly, but out of order
    a subject or object   the order is correct, but one noun phrase is inflected for another place
                          (it is read in the place its position implies), or the verb does not
                          agree with the subject (it is read as agreeing)
The last needs a fixed word order to say what a position implies, so free word order skips it.
A reinterpreted noun phrase or verb keeps the rest of its tags as spoken.
"""
from itertools import product

from .DialogRule import DialogRule


class DialogRuleMeaning:
    def __init__(self, accepts, order, text, subject_agreement, modifier_agreement, core_placements,
                 is_pro_drop=False, is_pro_drop_imperative=False, is_pro_drop_mandatory=False,
                 is_free_word_order=False, placement=('subjectivity', 'motion', 'role')):
        """
        accepts             part of speech → the parts of speech a speaker adds to it, as in `DialogLayout.ACCEPTS`
        order(reading)      the reading, its words in the order the language gives it
        text(node)          what a `DialogRule` tree reads as
        subject_agreement   tagaxes on which a verb agrees with its subject
        modifier_agreement  tagaxes on which a modifier agrees with its noun phrase
        core_placements     the places a noun phrase can be in for want of an adposition, such as
                            subject and direct object, as values of the `placement` tagaxes
        placement           tagaxes that say where a noun phrase sits in its clause
        """
        self.accepts = accepts
        self.order = order
        self.text = text
        self.subject_agreement = subject_agreement
        self.modifier_agreement = modifier_agreement
        self.core_placements = core_placements
        self.is_pro_drop = is_pro_drop
        self.is_pro_drop_imperative = is_pro_drop_imperative
        self.is_pro_drop_mandatory = is_pro_drop_mandatory
        self.is_free_word_order = is_free_word_order
        self.placement = placement
        self.modifies = {'np'}  # parts of speech whose added children are modifiers that agree with them

    def meaning(self, rule, strict=True) -> list:
        """Every meaning of the statement `rule`, as `DialogRule` trees whose nodes each list one
        tagpoint. Without `strict`, a statement that has none is read as if it had a single error."""
        readings = self._readings(rule, None, None)
        meanings = [reading for reading in readings if self._is_meaning(reading, True, True)]
        if strict or meanings:
            return meanings
        unique = {}
        for reading in [
            *(reading for reading in readings if self._is_meaning(reading, False, True)),
            *(reading for reading in readings if self._is_meaning(reading, True, False)),
            *([] if self.is_free_word_order else
              (reinterpreted for reading in readings for reinterpreted in self._reinterpreted(reading)
               if self._is_meaning(reinterpreted, True, True))),
        ]:
            unique.setdefault(self._key(reading), reading)
        return list(unique.values())

    def _is_added(self, parent, node) -> bool:
        return parent is not None and node.tag in self.accepts.get(parent.tag, ())

    def _readings(self, node, parent, index) -> list:
        """Every reading of `node`, whose parent's reading is `parent`. A node the speaker chose
        takes each of its tagpoints, but a modifier only those that agree with its noun phrase.
        A node that came with its parent takes the tagpoint at the parent's `index`."""
        if not isinstance(node, DialogRule):
            return [node]
        if parent is None or self._is_added(parent, node):
            indices = range(len(node.tags))
            if parent is not None and parent.tag in self.modifies:
                agreement = (*self.modifier_agreement, *self.placement)
                indices = [i for i in indices
                           if all(node.tags[i].get(tagaxis) == parent.tags[0].get(tagaxis) for tagaxis in agreement)]
        else:
            indices = [index]
        readings = []
        for i in indices:
            reading = DialogRule(node.tag, [node.tags[i]], [])
            for content in product(*(self._readings(child, reading, i) for child in node.content)):
                readings.append(DialogRule(node.tag, reading.tags, list(content)))
        return readings

    def _retagged(self, node, tags):
        """`node` and everything in it, read with `tags` in place of what they were spoken with."""
        if not isinstance(node, DialogRule):
            return node
        return DialogRule(node.tag, [{**node.tags[0], **tags}],
                          [self._retagged(child, tags) for child in node.content])

    def _reinterpreted(self, reading):
        """The reading with one phrase read as the place or agreement its inflection got wrong."""
        clause = reading
        nouns = [index for index, child in enumerate(clause.content) if getattr(child, 'tag', None) == 'np']
        verbs = [index for index, child in enumerate(clause.content) if getattr(child, 'tag', None) == 'vp']
        def with_phrase(index, phrase):
            return DialogRule(clause.tag, clause.tags, [*clause.content[:index], phrase, *clause.content[index + 1:]])
        for index in nouns:
            noun = clause.content[index]
            # Agreement within the phrase is its own; only where it sits is reinterpreted.
            if not self._are_modifiers_agreeing(noun):
                continue
            for place in self.core_placements:
                if place != self._place(noun):
                    yield with_phrase(index, self._retagged(noun, dict(zip(self.placement, place))))
        subjects = [child for child in clause.content
                    if getattr(child, 'tag', None) == 'np' and child.tags[0].get('subjectivity') == 'subject']
        for index in verbs:
            for subject in subjects[:1]:
                agreement = {tagaxis: subject.tags[0].get(tagaxis) for tagaxis in self.subject_agreement}
                yield with_phrase(index, self._retagged(clause.content[index], agreement))

    def _place(self, noun):
        return tuple(noun.tags[0].get(tagaxis) for tagaxis in self.placement)

    def _agree(self, a, b, tagaxes) -> bool:
        return all(a.tags[0].get(tagaxis) == b.tags[0].get(tagaxis) for tagaxis in tagaxes)

    def _are_modifiers_agreeing(self, noun) -> bool:
        return all(self._agree(modifier, noun, (*self.modifier_agreement, *self.placement))
                   for modifier in noun.content
                   if isinstance(modifier, DialogRule) and self._is_added(noun, modifier))

    def _is_meaning(self, clause, strict, ordered) -> bool:
        """Whether a reading is a meaning; `strict` enforces the language's rules for the subject,
        and `ordered` its word order."""
        phrases = [child for child in clause.content if isinstance(child, DialogRule)]
        verbs = [phrase for phrase in phrases if phrase.tag == 'vp']
        nouns = [phrase for phrase in phrases if phrase.tag == 'np']
        subjects = [noun for noun in nouns if noun.tags[0].get('subjectivity') == 'subject']
        places = [self._place(noun) for noun in nouns]
        if len(verbs) != 1 or len(subjects) > 1 or len(set(places)) != len(places):
            return False
        if strict:
            is_imperative = verbs[0].tags[0].get('mood') == 'imperative'
            is_droppable = self.is_pro_drop or (self.is_pro_drop_imperative and is_imperative)
            if (subjects and is_droppable and self.is_pro_drop_mandatory) or (not subjects and not is_droppable):
                return False
        if subjects and not self._agree(verbs[0], subjects[0], self.subject_agreement):
            return False
        if not all(self._are_modifiers_agreeing(noun) for noun in nouns):
            return False
        return not ordered or self.is_free_word_order or self.text(self.order(clause)) == self.text(clause)

    def _key(self, node):
        """What tells meanings apart: every node's part of speech, tags, and words."""
        if not isinstance(node, DialogRule):
            return node
        return (node.tag, tuple(sorted(node.tags[0].items())), tuple(self._key(child) for child in node.content))
