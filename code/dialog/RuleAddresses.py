# HUMAN VETTED

"""
An address is the position of each node in its parent's `content`, from the root
down: in a statement `clause{np{the red ball} vp{give}}`, `(0, 1)` is "red". The
statement's own address is `()`.

`Rule`s are mutable, but nothing here mutates one: every change rebuilds the `Rule`s
along the address and shares the rest, so earlier statements stay as they were.
"""
Address = tuple[int, ...]


class RuleAddresses:
    def resolve(self, root, address: Address):
        """The node at this address: a `Rule`, or a word as a string."""
        node = root
        for index in address:
            node = node.content[index]
        return node

    def replace(self, root, address: Address, node):
        """`root` with the node at this address replaced by `node`."""
        if not address:
            return node
        index, rest = address[0], address[1:]
        content = list(root.content)
        content[index] = self.replace(content[index], rest, node)
        return type(root)(root.tag, root.tags, content)

    def insert(self, root, parent: Address, index: int, node):
        """`root` with `node` inserted at `index` in the content of the `Rule` at `parent`."""
        rule = self.resolve(root, parent)
        return self.replace(root, parent, type(rule)(rule.tag, rule.tags, [*rule.content[:index], node, *rule.content[index:]]))

    def remove(self, root, address: Address):
        """`root` without the node at this address."""
        parent, index = address[:-1], address[-1]
        rule = self.resolve(root, parent)
        return self.replace(root, parent, type(rule)(rule.tag, rule.tags, [*rule.content[:index], *rule.content[index + 1:]]))
