"""Group generated inflections by text: the bundle text → tagpoints.

A text the player picks may have been rendered from several tagpoints (English
"give"), so each text keeps a `DictList` of every tagpoint that renders to it.

This module imports library modules: import it through
`adapter.LanguagesLibrary.import_module`.
"""
from tools.dictstores import DictList

from .listtrees import text


def bundle(generated, traversal, default):
    """(text → list tree, text → DictList of tagpoints) from `generate`'s (tags, tree) pairs.

    `traversal` is the one generated from; `default` is a DictSet that selects the
    inflection a newly placed word starts with, which comes first in both.
    """
    trees, tagpoints, first = {}, {}, None
    for tags, tree in generated:
        rendered = text(tree)
        if not rendered:
            continue
        trees.setdefault(rendered, tree)
        tagpoints.setdefault(rendered, []).append(tags)
        if first is None and tags in default:
            first = rendered
    if first is None:
        raise ValueError(f'{default.name} selects no inflection of {traversal.name}')
    order = [first, *(rendered for rendered in trees if rendered != first)]
    return ({rendered: trees[rendered] for rendered in order},
            {rendered: DictList(rendered, traversal.indexing, tagpoints[rendered]) for rendered in order})
