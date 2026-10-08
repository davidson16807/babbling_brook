class PaddedStringCodec:
    """Maps a string padded on one side to the same string without its padding.

    Decoding removes any repeats of `padding` from that side and restores exactly one; 
    `padding` may be any non-empty string and is matched whole, not as a set of characters.
    """
    def __init__(self, leftpad, rightpad):
        if not (leftpad or rightpad):
            raise ValueError("padding must be a non-empty string")
        self.leftpad = leftpad
        self.rightpad = rightpad
    def _unpad(self, text):
        if self.rightpad:
            while text.endswith(self.rightpad): text = text[:-len(self.rightpad)]
        if self.leftpad:
            while text.startswith(self.leftpad): text = text[len(self.leftpad):]
        return text
    def encode(self, content): return self._unpad(content)
    def decode(self, code): return (self.leftpad or '') + self._unpad(code) + (self.rightpad or '')
