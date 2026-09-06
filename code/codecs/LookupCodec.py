
class LookupCodec:
	def __init__(self, codec, key_id):
		self.codec = codec
		self.key_id = key_id
	def encode(self, content):
		return [[key, self.codec.encode(entry)] for key, entry in content] # TODO: use key_id here
	def decode(self, code):
		return {entry[self.key_id]: self.codec.decode(entry) for entry in code}
