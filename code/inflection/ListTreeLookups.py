"""Arrows on the inflections of a lexeme, kept as a function from tagpoints to list trees.

This module imports library modules: import it through
`adapter.LanguagesLibrary.import_module`.
"""
from tools.dictstores import DictList, DictLookup


class ListTreeLookups:
    """
    `ListTreeLookups` is a category whose objects are `DictLookup`s from tagpoints,
    such as the inflections of a lexeme, which map each tagpoint to the list tree it
    rendered as. Its arrows compose such a lookup with what a list tree reads as,
    restrict it to a mask, and invert it into a bundle and choose a section of that bundle.
    It is built from `ListTrees`, which reads list trees, and `DictBundles`, which inverts.
    """
    def __init__(self, list_trees, dict_bundles):
        self.list_trees = list_trees
        self.dict_bundles = dict_bundles

    def texts(self, trees):
        """`ListTrees.text` ∘ `trees`, for the tagpoints whose tree reads as some text."""
        texts = {tuplekey: self.list_trees.text(tree) for tuplekey, tree in trees.content.items()}
        return DictLookup(f'text∘({trees.name})', trees.indexing,
                          {tuplekey: text for tuplekey, text in texts.items() if text})

    def restrict(self, lookup, mask):
        """`lookup` on the tagpoints that `mask`, a `DictSet`, contains."""
        return DictLookup(f'({lookup.name})|({mask.name})', lookup.indexing,
                          {tuplekey: value for tuplekey, value in lookup.content.items()
                           if lookup.indexing.dictkey(tuplekey) in mask})

    def fibers(self, texts):
        """The bundle of `texts`: each text → a `DictList` of every tagpoint that reads as it."""
        return {text: DictList(text, texts.indexing, tuplekeys)
                for text, tuplekeys in self.dict_bundles.map_to_bundle(texts.content).items()}

    def section(self, fibers):
        """A section of the bundle `fibers`: each text → the first tagpoint in its fiber."""
        return {text: next(iter(tagpoints)) for text, tagpoints in fibers.items()}
