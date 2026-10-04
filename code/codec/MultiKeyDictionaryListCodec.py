class MultiKeyDictionaryListCodec:
    """Maps a list of objects to a dictionary that indexes each object under several keys.

    Each key is a tuple of attribute names, e.g. ('zone1', 'colorcode').
    Decoding rejects two different objects that claim the same key, since
    one of them would otherwise be silently dropped from the next save.
    Encoding lists each distinct object once, in order of first appearance.
    """
    def __init__(self, *keys):
        self.keys = keys
    def encode(self, content): return list(dict.fromkeys(content.values()))
    def decode(self, code):
        indexed = {}
        for item in code:
            for key in dict.fromkeys(tuple(getattr(item, name) for name in names) for names in self.keys):
                indexed[key] = item
        return indexed
