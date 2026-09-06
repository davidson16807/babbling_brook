# HUMAN WRITTEN

from typing import List

class DelimitedStringsCodec:
    def __init__(self, delimiter):
        self.delimiter = delimiter

    def encode(self, content: List[str]) -> str:
        return self.delimiter.join(item for item in content)

    def decode(self, code: str) -> List[str]:
        return [self.cells.decode(item.strip()) for item in code.split(self.delimiter)]

