"""Read the list trees that `ListTreeLanguage` renders, without importing the languages repo.

An inflection is kept as the list tree it rendered to, e.g. for "to the balls":

    [['np', ['adposition', 'to'], [['det', 'the'], ['n', 'balls']]]]
"""

PARTS = frozenset('np vp adposition det adj n v'.split())


def words(tree) -> list[tuple[str, str]]:
    """The words of a list tree, in order, each as (part, text).

    A list that starts with a part ('n', 'det', 'adposition', 'vp', ...) labels the
    words beneath it; other strings are words, such as the auxiliary "will" that
    English places directly in a verb phrase. '∅' marks a linguistic zero.
    A missing inflection is indicated by `None` and is rendered as '[MISSING]'.
    """
    result = []
    def walk(node, part):
        if isinstance(node, list):
            if node and isinstance(node[0], str) and node[0] in PARTS:
                part, node = node[0], node[1:]
            for child in node:
                walk(child, part)
        elif node is None:
            result.append((part, '[MISSING]'))
        else:
            text = ' '.join(str(node).replace('∅', '').split())
            if text:
                result.append((part, text))
    walk(tree, '')
    return result


def text(tree) -> str:
    return ' '.join(word for _, word in words(tree))


def kind(tree) -> str:
    """The outermost part of a list tree: 'np', 'vp', 'adj', ..., or '' if it has none."""
    if isinstance(tree, list):
        if tree and isinstance(tree[0], str) and tree[0] in PARTS:
            return tree[0]
        for child in tree:
            found = kind(child)
            if found:
                return found
    return ''
