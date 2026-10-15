"""The meanings a speaker could assign to a statement: its readings that are grammatically consistent.

A statement is a `DialogRule` tree whose nodes each list the tags of every homonym
they could be. A meaning is the same tree with one tagpoint chosen for each node,
so that every node's `tags` lists exactly one. `meaning` tries every combination
and keeps those that are grammatically self-consistent. It does not yet consider
the world the statement is said in.

Tagpoints are chosen per inflection the speaker chose, not per node: the words an
inflection came with, such as a noun phrase's article and noun, are read as the
same homonym as their phrase. Only the root, and what the speaker added to a node
(see `accepts`), are chosen independently.

A clause is consistent if it has exactly one verb phrase, exactly one subject, which
the verb agrees with, no two noun phrases in the same place (two direct objects, say),
and if every modifier agrees with the noun phrase it modifies, and is read as being in
the same place. Word order is not considered, so "the boy gives the ball" has two
meanings: either noun phrase could be the subject.
"""
from itertools import product

from .DialogRule import DialogRule


class DialogRuleMeaning:
    def __init__(self, accepts, subject_agreement, modifier_agreement,
                 placement=('subjectivity', 'motion', 'role')):
        """`accepts` is part of speech → the parts of speech a speaker adds to it, as in
        `DialogLayout.ACCEPTS`. `subject_agreement` and `modifier_agreement` are the tagaxes
        on which a verb agrees with its subject, and a modifier with its noun phrase.
        `placement` is the tagaxes that say where a noun phrase sits in its clause."""
        self.accepts = accepts
        self.subject_agreement = subject_agreement
        self.modifier_agreement = modifier_agreement
        self.placement = placement

    def meaning(self, rule) -> list:
        """Every grammatically consistent reading of the statement `rule`, as `DialogRule` trees
        whose nodes each list one tagpoint."""
        choices = self._choices(rule, None)
        meanings = []
        for picks in product(*(range(len(node.tags)) for node in choices)):
            reading = self._read(rule, dict(zip(map(id, choices), picks)), 0)
            if self._is_consistent(reading):
                meanings.append(reading)
        return meanings

    def _is_added(self, parent, node) -> bool:
        return parent is not None and node.tag in self.accepts.get(parent.tag, ())

    def _choices(self, node, parent) -> list:
        """The nodes whose tagpoint is chosen independently: the root, and everything added."""
        if not isinstance(node, DialogRule):
            return []
        own = [node] if parent is None or self._is_added(parent, node) else []
        return own + [choice for child in node.content for choice in self._choices(child, node)]

    def _read(self, node, picks, index):
        """`node` with the tagpoint each choice picked; a node that is not a choice takes its parent's."""
        if not isinstance(node, DialogRule):
            return node
        index = picks.get(id(node), index)
        return DialogRule(node.tag, [node.tags[index]],
                          [self._read(child, picks, index) for child in node.content])

    def _agree(self, a, b, tagaxes) -> bool:
        return all(a.tags[0].get(tagaxis) == b.tags[0].get(tagaxis) for tagaxis in tagaxes)

    def _is_consistent(self, clause) -> bool:
        phrases = [child for child in clause.content if isinstance(child, DialogRule)]
        verbs = [phrase for phrase in phrases if phrase.tag == 'vp']
        nouns = [phrase for phrase in phrases if phrase.tag == 'np']
        subjects = [noun for noun in nouns if noun.tags[0].get('subjectivity') == 'subject']
        places = [tuple(noun.tags[0].get(tagaxis) for tagaxis in self.placement) for noun in nouns]
        return (len(verbs) == 1 and len(subjects) == 1
                and self._agree(verbs[0], subjects[0], self.subject_agreement)
                and len(set(places)) == len(places)
                and all(self._agree(modifier, noun, (*self.modifier_agreement, *self.placement))
                        for noun in nouns for modifier in noun.content
                        if isinstance(modifier, DialogRule) and self._is_added(noun, modifier)))
