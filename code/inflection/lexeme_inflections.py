"""What the inventory and inflection grid need of one lexeme.

This module imports library modules: import it through
`adapter.LanguagesLibrary.import_module`.
"""
from tools.dictbundles import DictBundles
from tools.dictstores import DictList

from .ListTrees import ListTrees

dict_bundles = DictBundles()
list_trees = ListTrees()


def lexeme_inflections(generated, traversal, default):
    """(text → list tree, text → DictList of tagpoints) from `generate`'s (tags, tree) pairs.

    The tagpoints of a text are the fiber over it in the bundle of the function
    tagpoint → text, so a homonym such as English "give" keeps every interpretation.
    Texts that render empty are left out, since there is nothing to show. Each text
    keeps the first list tree rendered as it. `traversal` is the one generated from;
    `default` is a DictSet that selects the inflection a newly placed word starts
    with, which comes first in both.
    """
    texts, trees = {}, {}
    for tags, tree in generated:
        tuplekey = traversal.indexing.tuplekey(tags)
        texts[tuplekey] = list_trees.text(tree)
        trees.setdefault(texts[tuplekey], tree)
    bundle = dict_bundles.map_to_bundle(texts)
    bundle.pop('', None)
    first = next((text for tuplekey, text in texts.items()
                  if text and traversal.indexing.dictkey(tuplekey) in default), None)
    if first is None:
        raise ValueError(f'{default.name} selects no inflection of {traversal.name}')
    order = [first, *(text for text in bundle if text != first)]
    return ({text: trees[text] for text in order},
            {text: DictList(text, traversal.indexing, bundle[text]) for text in order})
