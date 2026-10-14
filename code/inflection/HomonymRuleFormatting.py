"""Cast a `HomonymRule` tree to a string of natural language.

A stripped-down `RuleFormatting` from the languages repo, with the same output for
what the dialog uses: words are joined by spaces, '∅' (a linguistic zero) reads as
nothing, spaces around an affix delimiter are removed so that "ball -ga" reads as
"ball-ga", and a word the language could not inflect (`None`) reads as '[MISSING]'.
Anki clozes, parentheses, brackets, and diagnostics are left out.
"""
import re

from .HomonymRule import HomonymRule


class HomonymRuleFormatting:
    def __init__(self, affix_delimiter='-'):
        self.affix_delimiter = affix_delimiter
        self.affix_regex = re.compile(r'\s*-\s*')

    def format(self, node) -> str:
        """What a `HomonymRule` tree, or a word in one, reads as."""
        if node is None:
            return '[MISSING]'
        text = (' '.join(self.format(child) for child in node.content)
                if isinstance(node, HomonymRule) else node)
        text = self.affix_regex.sub(self.affix_delimiter, text.replace('∅', ' '))
        return ' '.join(text.split())
