# HUMAN WRITTEN

class PrimitiveListCodec:
	def __init__(self, type):
		self.type = type
		self.item_count = 1
	def encode(self, content): return [str(content)]
	def decode(self, code): return self.type(code[0])

class BooleanListCodec:
	def __init__(self, truth_text='x'):
		self.truth_text =truth_text
		self.item_count = 1
	def encode(self, content): return [self.truth_text if content else '']
	def decode(self, code): return bool(code[0])
