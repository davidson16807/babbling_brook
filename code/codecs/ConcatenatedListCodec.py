# HUMAN WRITTEN

class ConcatenatedListCodec:
	def __init__(self, *codecs):
		self.codecs = codecs
	def encode(self, content:list)->list[str]: 
		decoded = content
		encoded = []
		for codec in self.codecs:
			encoded = [*encoded, *codec.encode(decoded[0])]
			decoded = decoded[1:]
		return encoded
	def decode(self, code:list[str])->list: 
		encoded = code
		decoded = []
		for codec in self.codecs:
			decoded = [*decoded, codec.decode(encoded)]
			encoded = encoded[codec.item_count:]
		return decoded
