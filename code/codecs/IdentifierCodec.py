import json


class IdentifierCodec:
    """JSON scalar cells distinguish integer IDs from string IDs on round-trip."""

    def encode(self, content):
        if type(content) not in (str, int):
            raise ValueError("Identifiers must be strings or integers")
        return json.dumps(content, ensure_ascii=False)

    def decode(self, code):
        content = json.loads(code)
        if type(content) not in (str, int):
            raise ValueError("Identifiers must be strings or integers")
        return content
