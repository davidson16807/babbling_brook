# HUMAN VETTED

class ConcatenatedContainerCodec:
    def __init__(self, Container, *codecs):
        self.Container = Container
        self.codecs = codecs
        self.item_count = sum(codec.item_count for codec in codecs)

    def encode(self, content):
        values = list(content)
        return [cell for codec, value in zip(self.codecs, values)
                for cell in codec.encode(value)]

    def decode(self, code):
        decoded, offset = [], 0
        for codec in self.codecs:
            decoded.append(codec.decode(code[offset:offset + codec.item_count]))
            offset += codec.item_count
        return self.Container(decoded)
