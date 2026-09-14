
class PrefixedStringCodec:
	def __init__(self, prefix):
		self.prefix = prefix
	def encode(self, content): return self.prefix + content
	def decode(self, code): return code if not code.startswith(self.prefix) else code[len(self.prefix):]
