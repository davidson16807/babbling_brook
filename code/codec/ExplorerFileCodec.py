from .ComposedCodec import ComposedCodec
from .DelimitedStringsCodec import DelimitedStringsCodec
from .EscapedTextCodec import EscapedTextCodec
from .MappedCodec import MappedCodec


class ExplorerFileCodec:
    """Named TSV tables. Unknown sections survive decoding; consumers validate names."""

    def __init__(self):
        self.row = ComposedCodec(MappedCodec(EscapedTextCodec()), DelimitedStringsCodec('\t'))

    def encode(self, content):
        sections = []
        for name, rows in content.items():
            if not name or any(c in name for c in '\n\r\t') or name != name.strip():
                raise ValueError("Invalid section name")
            self._validate(name, rows)
            lines = [self.row.encode(row) for row in rows]
            if any(line.lstrip().startswith('#') or not line.strip() for line in lines):
                raise ValueError("A row cannot be blank or begin with a comment marker")
            sections.append('\n'.join([f'# {name}', *lines]))
        return '\n\n'.join(sections) + '\n'

    def decode(self, code):
        sections, current, blank = {}, None, True
        for line in code.splitlines():
            if not line.strip():
                blank = True
                continue
            if blank and line.startswith('# '):
                name = line[2:].strip()
                if not name or name in sections:
                    raise ValueError(f"Invalid or duplicate section: {name!r}")
                sections[name] = []
                current = name
            elif not line.lstrip().startswith('#'):
                if current is None:
                    raise ValueError("Table row before first section")
                sections[current].append(self.row.decode(line))
            blank = False
        for name, rows in sections.items():
            self._validate(name, rows)
        return sections

    def _validate(self, name, rows):
        if not rows or not rows[0] or len(set(rows[0])) != len(rows[0]):
            raise ValueError(f"Missing or duplicate columns in {name}")
        if any(len(row) != len(rows[0]) for row in rows):
            raise ValueError(f"Malformed row width in {name}")
