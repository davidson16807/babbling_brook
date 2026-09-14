# HUMAN VETTED

from .ConcatenatedContainerCodec import ConcatenatedContainerCodec

class ObjectListCodec:
    def __init__(self, Class, *attribute_codecs):
        self.Class = Class
        self.headers = [header for header, _ in attribute_codecs]
        self.codecs = [codec for _, codec in attribute_codecs]
        self.values = ConcatenatedContainerCodec(list, *self.codecs)
        self.item_count = self.values.item_count

    def encode(self, content):
        return self.values.encode([getattr(content, header) for header in self.headers])

    def decode(self, code):
        return self.Class(**dict(zip(self.headers, self.values.decode(code))))
