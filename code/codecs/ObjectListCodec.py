# HUMAN WRITTEN

class ObjectListCodec:
	def __init__(self, Class, *attribute_codecs):
		self.Class = Class
		self.headers = [header for header, codec in attribute_codecs]
		self.codecs = [codec for header, codec in attribute_codecs]
		self.item_count = len(attribute_codecs)
	def encode(self, content) -> list[str]:
		decoded = [getattr(content,header) for header in self.headers]
		encoded = []
		for codec in self.codecs:
			encoded = [*encoded, *codec.encode(decoded[0])]
			decoded = decoded[1:]
		return encoded
	def decode(self, code: list[str]):
		encoded = code
		decoded = []
		for codec in self.codecs:
			decoded = [*decoded, codec.decode(encoded)]
			encoded = encoded[codec.item_count:]
		return self.Class(**dict(zip(self.headers, decoded)))
