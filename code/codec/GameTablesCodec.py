from types import SimpleNamespace

from .CommentedStringCodec import CommentedStringCodec
from .ComposedCodec import ComposedCodec
from .ConcatenatedContainerCodec import ConcatenatedContainerCodec
from .DelimitedStringsCodec import DelimitedStringsCodec
from .DictionaryListCodec import DictionaryListCodec
from .EscapedTextCodec import EscapedTextCodec
from .MappedCodec import MappedCodec
from .PrefixedStringCodec import PrefixedStringCodec


class GameTablesCodec:
    """Codec for a mapping of named, rectangular TSV tables.

    Unknown sections survive decoding so that a game-specific consumer can
    decide which table names it supports.
    """

    def __init__(self):
        self.row = ComposedCodec(
            MappedCodec(EscapedTextCodec()),
            DelimitedStringsCodec('\t'),
        )

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


# The old name remains public so existing callers and files stay compatible.
GameFileCodec = GameTablesCodec


def GameRowCodec(key_codec, value_codec, column_delimiter='\t'):
    return ComposedCodec(
        ConcatenatedContainerCodec(list, key_codec, value_codec),
        MappedCodec(EscapedTextCodec()),
        DelimitedStringsCodec(column_delimiter),
    )


def GameTableCodec(
        header,
        key_codec,
        value_codec,
        column_delimiter='\t',
        row_delimiter='\n',
        comment_delimiter='#'):
    """Build a codec for one of the legacy game-format dictionary tables."""

    return ComposedCodec(
        DictionaryListCodec(),
        MappedCodec(GameRowCodec(
            key_codec,
            value_codec,
            column_delimiter=column_delimiter,
        )),
        DelimitedStringsCodec(row_delimiter),
        CommentedStringCodec(comment_delimiter),
        PrefixedStringCodec(header + row_delimiter),
        SimpleNamespace(
            encode=lambda code: code.rstrip(row_delimiter),
            decode=lambda code: code.strip(row_delimiter) + row_delimiter,
            item_count=1,
        ),
    )
