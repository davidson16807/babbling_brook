# HUMAN WRITTEN

class ContainerListCodec:
	def __init__(self, Container, Item, item_count):
		self.Container = Container
		self.Item = Item
		self.item_count = item_count
	def encode(self, content): return [str(item) for item in content]
	def decode(self, code): return self.Container([self.Item(item) for item in code[:self.item_count]])
