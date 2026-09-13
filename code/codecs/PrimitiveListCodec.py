# HUMAN WRITTEN

class PrimitiveListCodec:
	def __init__(self, type):
		self.type = type
		self.item_count = 1
	def encode(self, content): return [str(content)]
	def decode(self, code): return self.type(code[0])
