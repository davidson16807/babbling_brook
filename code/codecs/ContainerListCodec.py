# HUMAN WRITTEN

class ContainerListCodec:
	def __init__(self, Container, Item, item_count):
		self.Container = Container
		self.item_count = item_count
	def encode(self, content): return [str(content[i]) for i in range(self.item_count)]
	def decode(self, code): return Container(Item(content[i]) for i in range(self.item_count))
