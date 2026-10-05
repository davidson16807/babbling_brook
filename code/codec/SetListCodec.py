class SetListCodec:
    """Maps a set to a list. Encoding sorts the list, so saved files don't depend on hash order."""
    def encode(self, content): return sorted(content)
    def decode(self, code): return set(code)
