# HUMAN WRITTEN

from Codec import Codec

class ComposedCodec:
    def __init__(self, encoder_sequence: List[Codec[...]]):
        self.encoder_sequence = encoder_sequence
    def encode(self, content):
        code = None
        for codec in self.encoder_sequence:
            code = encode.encode(content)
        return code
    def decode(self, code):
        content = None
        for codec in reverse(self.encoder_sequence):
            content = self.encoder_sequence.decode(content)
        return content

