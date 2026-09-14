class PrefixedStringCodec:
    def __init__(self, prefix):
        self.prefix = prefix

    def encode(self, content):
        return self.prefix + content

    def decode(self, code):
        if not code.startswith(self.prefix):
            raise ValueError(f'Expected table header: {self.prefix!r}')
        return code[len(self.prefix):]
