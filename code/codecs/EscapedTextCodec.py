class EscapedTextCodec:
    """Escape cell delimiters, preserving literal hashes and whitespace.

    Comments and section headers are interpreted by the table codec, where
    their position is known. Sequential replacements would corrupt literal
    backslashes followed by t, n, or r; decode consumes each escape once.
    """

    escapes = {"\\": "\\\\", "\t": "\\t", "\n": "\\n", "\r": "\\r"}
    replacements = {"\\": "\\", "t": "\t", "n": "\n", "r": "\r"}

    def encode(self, content: str) -> str:
        return "".join(self.escapes.get(character, character) for character in content)

    def decode(self, code: str) -> str:
        content = []
        characters = iter(code)
        for character in characters:
            if character == "\\":
                escaped = next(characters, None)
                if escaped not in self.replacements:
                    raise ValueError(f"Invalid text escape: {escaped!r}")
                character = self.replacements[escaped]
            content.append(character)
        return "".join(content)
