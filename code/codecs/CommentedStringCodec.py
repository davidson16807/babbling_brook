# HUMAN WRITTEN

import re

class CommentedStringCodec:
	def __init__(self, escape='#'):
		self.pattern = re.compile(r'\n?'+escape+r'[^\n]*')
	def encode(self, content): return content
	def decode(self, code): return re.sub(self.pattern, '', code).strip('\n')
