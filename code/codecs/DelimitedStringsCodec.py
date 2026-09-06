class DelimitedStringsCodec:
    def __init__(self, delimiter: str):
        self.delimiter = delimiter

    def encode(self, content: list[str]) -> str:
        return self.delimiter.join(content)

    def decode(self, code: str) -> list[str]:
        # Preserve spaces and empty cells. Escape embedded delimiters first.
        return code.split(self.delimiter)
