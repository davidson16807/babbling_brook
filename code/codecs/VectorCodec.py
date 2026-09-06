class VectorCodec:
    """A whitespace-separated scalar cell for a supplied PyGLM vector type."""

    def __init__(self, vector_type):
        self.vector_type = vector_type
        self.size = len(vector_type())

    def encode(self, content):
        if len(content) != self.size:
            raise ValueError("Unexpected vector size")
        return " ".join(repr(value) for value in content)

    def decode(self, code):
        values = code.split()
        if len(values) != self.size:
            raise ValueError("Unexpected vector size")
        return self.vector_type(*(float(value) for value in values))
