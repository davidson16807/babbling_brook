class OptionalValueListCodec:
    """One cell holding a value or nothing.

    An empty cell represents an absent reference (including map ID zero).
    """
    def __init__(self, type):
        self.type = type
        self.item_count = 1
    def encode(self, content): return ['' if content is None else str(content)]
    def decode(self, code): return None if code[0] == '' else self.type(code[0])
