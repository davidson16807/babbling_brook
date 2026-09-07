import unittest
from bootstrap import ROOT
from babbling_brook.codecs.GameFileCodec import GameFileCodec
from babbling_brook.codecs.IdentifierCodec import IdentifierCodec
from babbling_brook.codecs.ComponentsCodec import ComponentsCodec
from babbling_brook.codecs.ComposedCodec import ComposedCodec
from babbling_brook.codecs.DelimitedStringsCodec import DelimitedStringsCodec
from babbling_brook.codecs.EscapedTextCodec import EscapedTextCodec
from babbling_brook.codecs.MappedCodec import MappedCodec
from babbling_brook.codecs.ZippedCodec import ZippedCodec
from babbling_brook.codecs.maps.PpmImageCodec import PpmImageCodec
from dataclasses import dataclass


class CodecTests(unittest.TestCase):
    def test_save_cell_round_trip(self):
        codec = GameFileCodec()
        content = {'inventory': [['item', 'quantity'], [' leading #hash\\t\t\n\r\\ trailing ', '3']],
                   'empty': [['column']]}
        self.assertEqual(codec.decode(codec.encode(content)), content)

    def test_comments_and_unknown_sections(self):
        code = '# format\nkey\tvalue\nversion\t1\n  # ordinary comment\n\n# future\na\tb\nx#y\tz\n'
        self.assertEqual(GameFileCodec().decode(code)['future'][1], ['x#y', 'z'])

    def test_malformed_sections_rejected(self):
        for code in ('# a\nx\ty\n1\n', '# a\nx\n\n# a\nx\n', 'x\ty\n', '# a\nx\nx\\q\n'):
            with self.subTest(code=code), self.assertRaises(ValueError):
                GameFileCodec().decode(code)

    def test_identifier_types(self):
        codec = IdentifierCodec()
        for value in (1, '1', 'player', '(2, 4)'):
            self.assertEqual(codec.decode(codec.encode(value)), value)
        with self.assertRaises(ValueError):
            codec.decode('true')

    def test_composed_component_tables(self):
        @dataclass(frozen=True)
        class Foo:
            bar: int
            baz: str
        codec = ComposedCodec(
            ZippedCodec(ComponentsCodec('Foo', Foo, [('bar', int), ('baz', str)])),
            MappedCodec(MappedCodec(MappedCodec(EscapedTextCodec()))),
            MappedCodec(MappedCodec(DelimitedStringsCodec('\t'))),
            MappedCodec(DelimitedStringsCodec('\n')), DelimitedStringsCodec('\n\n'))
        content = [[Foo(2, 'a\tb\\n')]]
        self.assertEqual(codec.decode(codec.encode(content)), content)

    def test_ppm_and_sample_data(self):
        image = PpmImageCodec().decode((ROOT / 'data/world.ppm').read_text())
        self.assertEqual((image.width, image.height, len(image.pixels)), (18, 18, 324))
        self.assertIn('objects', GameFileCodec().decode((ROOT / 'data/world.game').read_text()))
        for code in ('P6 1 1 255 0 0 0', 'P3 1 1 255 0 0', 'P3 1 1 2 3 0 0'):
            with self.assertRaises(ValueError):
                PpmImageCodec().decode(code)


if __name__ == '__main__':
    unittest.main()
