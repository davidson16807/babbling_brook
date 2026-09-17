"""Named TSV sections and typed rows, independent of any game's schema.

Decoded sections contain a header row followed by data rows. Both ordinary and
comment-prefixed headers are accepted, including the existing Babbling Brook
files. Unknown section names are preserved for the application to interpret.
"""
from types import SimpleNamespace

from .ComposedCodec import ComposedCodec
from .ConcatenatedContainerCodec import ConcatenatedContainerCodec
from .DictionaryListCodec import DictionaryListCodec
from .DelimitedStringsCodec import DelimitedStringsCodec
from .EscapedTextCodec import EscapedTextCodec
from .MappedCodec import MappedCodec
from .CommentedStringCodec import CommentedStringCodec
from .PrefixedStringCodec import PrefixedStringCodec


class GameTablesCodec:
    def __init__(self):
        self.row = ComposedCodec(MappedCodec(EscapedTextCodec()), DelimitedStringsCodec('\t'))

    def encode(self, tables):
        sections = []
        for name, rows in tables.items():
            self._validate_name(name)
            self._validate(name, rows)
            lines = [self.row.encode(row) for row in rows]
            if any(line.lstrip().startswith('#') or not line.strip() for line in lines):
                raise ValueError("A row cannot be blank or begin with a comment marker")
            sections.append('\n'.join([f'# {name}', *lines]))
        return '\n\n'.join(sections) + ('\n' if sections else '')

    def decode(self, text):
        sections, current, blank = {}, None, True
        for line in text.splitlines():
            if not line.strip():
                blank = True
                continue
            if blank and line.startswith('# '):
                name = line[2:].strip()
                self._validate_name(name)
                if name in sections:
                    raise ValueError(f"Duplicate section: {name!r}")
                sections[name] = []
                current = name
            elif line.lstrip().startswith('#'):
                # Legacy headers are comments with tab-separated column names.
                # Ordinary comments do not supply a table header.
                if current is not None and not sections[current] and '\t' in line:
                    sections[current].append(self.row.decode(line.lstrip()[1:].lstrip(' ')))
            else:
                if current is None:
                    raise ValueError("Table row before first section")
                sections[current].append(self.row.decode(line))
            blank = False
        for name, rows in sections.items():
            self._validate(name, rows)
        return sections

    @staticmethod
    def _validate_name(name):
        if not name or any(c in name for c in '\n\r\t') or name != name.strip():
            raise ValueError("Invalid section name")

    @staticmethod
    def _validate(name, rows):
        if not rows or not rows[0] or any(not column for column in rows[0]) or len(set(rows[0])) != len(rows[0]):
            raise ValueError(f"Missing or duplicate columns in {name}")
        if any(len(row) != len(rows[0]) for row in rows):
            raise ValueError(f"Malformed row width in {name}")


class TypedGameTableCodec:
    """Convert a header and string rows to a dictionary of typed key/value pairs."""
    def __init__(self, columns, key_codec, value_codec):
        self.columns = list(columns)
        self.pair = ConcatenatedContainerCodec(tuple, key_codec, value_codec)
        if len(self.columns) != self.pair.item_count:
            raise ValueError("Columns must match the row codec width")

    def encode(self, table):
        return [self.columns.copy(), *(self.pair.encode(item) for item in table.items())]

    def decode(self, rows):
        if rows[0] != self.columns:
            raise ValueError(f"Expected columns: {self.columns}")
        table = {}
        for row in rows[1:]:
            if len(row) != self.pair.item_count:
                raise ValueError("Malformed row width")
            key, value = self.pair.decode(row)
            if key in table:
                raise ValueError(f"Duplicate key: {key!r}")
            table[key] = value
        return table


# Legacy row/table factories remain available for existing imports.
def GameRowCodec(key_codec, value_codec, column_delimiter='\t'):
	return ComposedCodec(
		ConcatenatedContainerCodec(list, key_codec, value_codec),
		MappedCodec(EscapedTextCodec()),
		DelimitedStringsCodec(column_delimiter),
	)

def GameTableCodec(header, key_codec, value_codec,
		column_delimiter='\t', row_delimiter='\n', comment_delimiter='#'):
	return ComposedCodec(
			DictionaryListCodec(),
			MappedCodec(GameRowCodec(key_codec, value_codec, column_delimiter=column_delimiter)),
			DelimitedStringsCodec(row_delimiter),
			CommentedStringCodec(comment_delimiter),
			PrefixedStringCodec(header+row_delimiter),
			SimpleNamespace(
				encode=lambda code: code.rstrip(row_delimiter), 
				decode=lambda code: code.strip(row_delimiter)+row_delimiter, 
				item_count=1),
		)

