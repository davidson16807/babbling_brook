# HUMAN WRITTEN

class ZippedCodec:
    def __init__(self, *codecs):
        self.codecs = codecs
    def encode(self, content):
        return [codec.encode(item)
                for codec, item in zip(self.codecs, content, strict=True)]
    def decode(self, code):
        return [codec.decode(item)
                for codec, item in zip(self.codecs, code, strict=True)]
