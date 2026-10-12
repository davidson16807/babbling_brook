"""
"trees.py" contains representations for the nodes of abstract syntax trees.
"""

class Rule:
    def __init__(self, tag, tags, content):
        self.tag = tag
        self.tags = tags
        self.content = content
    def __getitem__(self, key):
        if type(key) is int:
            return self.content[key]
        else:
            return self.tags[key] if key in self.tags else None
    def __setitem__(self, key):
        if type(key) is int:
            self.content[key] = key
            return self.content[key]
        else:
            self.tags[key] = key
            return self.tags[key]
    def __str__(self):
        return '' + self.tag + '{'+' '.join([str(member) for member in self.content])+'}'
    def __repr__(self):
        return ' '.join([
                self.tag,
                '{'+' '.join([str(member) for member in self.content])+'}',
                '\n'.join(['{', *[f'  {key}:{self.tags[key]}' for key in sorted(self.tags.keys())], '}']),
            ])
