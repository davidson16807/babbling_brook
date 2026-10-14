# HUMAN VETTED

"""
`DialogRule` is much like `Rule` of the languages repo,
but it is specially designed for use with the dialog GUI in Babbling Brook.
In particular, its `tags` attribute represent one-to-many homonymous tagpoints,
which simplifies the interpretation of user statements for validity and meaning.
"""


class DialogRule:
    def __init__(self, tag, tags, content):
        self.tag = tag
        self.tags = tags        # list of dicts: tagaxis → tag, one per homonym
        self.content = content  # words (strings) and `DialogRule`s

    def __str__(self):
        return '' + self.tag + '{'+' '.join([str(member) for member in self.content])+'}'

    def __repr__(self):
        return ' '.join([
                self.tag,
                '{'+' '.join([str(member) for member in self.content])+'}',
                '\n'.join(['{', *[f'  {key}:{self.tags[key]}' for key in sorted(self.tags.keys())], '}']),
            ])
