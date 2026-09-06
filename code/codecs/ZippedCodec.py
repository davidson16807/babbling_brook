# HUMAN WRITTEN

from typing import List

class ZippedCodec:
    def __init__(self, *codecs):
        self.codecs = codecs
    def encode(self, content: List[...]):
        return [codec.encode(item) 
            for codec, item in zipped(self.codecs, content)]
    def decode(self, code: List[...]):
        return [codec.decode(item) 
            for codec, item in zipped(self.codecs, code)]

