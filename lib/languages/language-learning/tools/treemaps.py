from .nodes import Rule

"""
"trees.py" contains functionality used to manipulate abstract syntax trees.

Two representations for syntax trees are available:
* syntax trees where nodes are simple python lists ("ListTrees")
* syntax trees where nodes are instances of a custom data type, "Rule" ("RuleTrees")

Both representations have their advantages.
ListTrees make it easy to perform simple operations like node replacement
RuleTrees condense ListTrees down to a form where it is easy to rearrange 
  grammatical elements based on tagaxes such as semantic role.
"""

class ListTreeMap:
    """
    `ListTrees` captures the transformation of tree like structures that are made out of lists.
    Its functionality is roughly comparable to that of the Lisp programming language.
    The content of lists is roughly comparable to that of the phase marker notation used in linguiustics:
        https://en.wikipedia.org/wiki/Parse_tree#Phrase_markers
    """
    def __init__(self, operations={}):
        self.operations = operations
    def map(self, tree, context={}):
        def wrap(x): 
            return x if isinstance(x, list) else [x]
        if len(tree) < 1: return tree
        opcode = tree[0]
        operands = tree[1:]
        return ([self.map(opcode, context), 
                *wrap(self.map(operands, context))] if isinstance(opcode, list)
            else self.operations[opcode](self, tree, context) if opcode in self.operations
            else [opcode, *wrap(self.map(operands, context))])

class RuleTreeMap:
    """
    `RuleTrees` performs functionality analogous to ListTrees 
    when transforming nested syntax trees that are made out of `Rule` objects.
    """
    def __init__(self, operations={}):
        self.operations = operations
    def map(self, rule, context={}):
        return ([self.map(subrule) for subrule in rule] if isinstance(rule, list)
            else rule if not isinstance(rule, Rule)
            else self.operations[rule.tag](self, rule) if rule.tag in self.operations
            else Rule(rule.tag, rule.tags, self.map(rule.content)))
