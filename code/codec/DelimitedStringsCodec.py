# HUMAN WRITTEN

import re

class DelimitedStringsCodec:
    def __init__(self, delimiter: str, regex_delimiter = None, postfixed=False):
        self.delimiter = delimiter
        self.regex_delimiter = regex_delimiter
        self.postfixed = postfixed
    def encode(self, content: list[str]) -> str:
        return self.delimiter.join(content)
    def decode(self, code: str) -> list[str]:
        if not code: return []
        decoded = re.split(self.regex_delimiter, code) if self.regex_delimiter else code.split(self.delimiter)
        decoded = decoded[:-1] if not decoded[-1] and self.postfixed else decoded
        return decoded
