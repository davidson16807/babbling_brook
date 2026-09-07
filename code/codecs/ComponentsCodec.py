class ComponentsCodec:
    """Convert a component sequence to a headed table of scalar cells.

    Fields are (attribute, callable-or-codec) pairs; framing/escaping is composed
    outside this codec. A codec supplies encode/decode, a callable parses text.
    """

    def __init__(self, name, component_type, fields):
        self.name, self.component_type, self.fields = name, component_type, fields

    def encode(self, content):
        rows = [[name for name, _ in self.fields]]
        for item in content:
            rows.append([codec.encode(getattr(item, name)) if hasattr(codec, 'encode') and hasattr(codec, 'decode')
                         else str(getattr(item, name)) for name, codec in self.fields])
        return rows

    def decode(self, code):
        if not code or code[0] != [name for name, _ in self.fields]:
            raise ValueError(f"Invalid columns in {self.name}")
        result = []
        for row in code[1:]:
            if len(row) != len(self.fields):
                raise ValueError(f"Invalid row width in {self.name}")
            values = [codec.decode(cell) if hasattr(codec, 'decode') else codec(cell)
                      for (_, codec), cell in zip(self.fields, row)]
            result.append(self.component_type(*values))
        return result
