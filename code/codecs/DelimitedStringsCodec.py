# HUMAN WRITTEN

class DelimitedStringsCodec:
    def __init__(self, delimiter: str, postfixed=False):
        self.delimiter = delimiter
        self.postfixed = postfixed
    def encode(self, content: list[str]) -> str:
        return self.delimiter.join(content)
    def decode(self, code: str) -> list[str]:
        if not code: return []
        decoded = code.split(self.delimiter)
        decoded = decoded[:-1] if not decoded[-1] and self.postfixed else decoded
        return decoded
