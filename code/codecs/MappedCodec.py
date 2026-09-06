# HUMAN WRITTEN

from typing import List

class MappedCodec:
    def __init__(self, codec):
        self.codec = codec

    def encode(self, content):
        return [self.codec.encode(item) for item in content]

    def decode(self, code):
        return [self.codec.decode(item) for item in code]
