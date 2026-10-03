class DefaultValueListCodec:
    """One cell holding a value, where an empty cell means `default`.

    Spreadsheet trait cells may omit a numeric value to use its default.
    Encoding always writes the value, so a round trip makes the default explicit.
    """
    def __init__(self, type, default):
        self.type = type
        self.default = default
        self.item_count = 1
    def encode(self, content): return [str(content)]
    def decode(self, code): return self.default if code[0] == '' else self.type(code[0])
