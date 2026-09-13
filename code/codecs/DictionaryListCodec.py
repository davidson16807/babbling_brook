# HUMAN WRITTEN

class DictionaryListCodec:
	def __init__(self): pass
	def encode(self, content): return list(content.items())
	def decode(self, code): return dict(code)
