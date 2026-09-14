# HUMAN WRITTEN

class ComposedCodec:
    def __init__(self, *encoder_sequence):
        self.encoder_sequence = encoder_sequence
        self.item_count = 1
    def encode(self, content):
        for codec in self.encoder_sequence:
            content = codec.encode(content)
        return content
    def decode(self, code):
        for codec in reversed(self.encoder_sequence):
            code = codec.decode(code)
        return code
