
class LookupCodec:
	def __init__(self, codec, key: str|int):
		self.codec = codec
		self.key = key
	def encode(self, content):
		return [[key, self.codec.encode(entry)] for key, entry in content] # TODO: use key here
	def decode(self, code):
		return {entry[self.key]: self.codec.decode(entry) for entry in code}
