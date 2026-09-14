from collections import defaultdict
import unittest
from dataclasses import dataclass, replace
from pathlib import Path

from pyglm import glm

from babbling_brook.codecs import (
    ComposedCodec, DelimitedStringsCodec, EscapedTextCodec,
    MappedCodec, ZippedCodec,
)
from babbling_brook.codecs.GameFileCodec import GameFileCodec
from babbling_brook.codecs.GameStateCodec import (
    GameStateCodec, PluginListCodec, GameTableCodec, _codec,
)
from babbling_brook.codecs.PrimitiveListCodec import PrimitiveListCodec
from babbling_brook.codecs.ContainerListCodec import ContainerListCodec
from babbling_brook.codecs.ObjectListCodec import ObjectListCodec
from babbling_brook.codecs.maps.MapCodec import MapCodec
from babbling_brook.codecs.maps.ObjectPlacementCodec import ObjectPlacementCodec
from babbling_brook.codecs.maps.PpmImageCodec import PpmImageCodec
from babbling_brook.model import GameState, PluginOps
from babbling_brook.model.components.archetypes import TileArchetype
from babbling_brook.model.components.instances import CharacterAnimationState, ObjectPlacement, VerticalPhysics
from babbling_brook.model.stores import ArchetypeComponentStores, InstanceComponentStores


@dataclass(frozen=True)
class Foo:
    bar: int
    baz: str


@dataclass(frozen=True)
class Qux:
    norf: float


def table(name, cls, attributes):
    key = PrimitiveListCodec(str)
    return GameTableCodec('# ' + name + '\nentity\t' + '\t'.join(name for name, _ in attributes),
                          key, ObjectListCodec(cls, *attributes))


def tables():
    return (table('Foo', Foo, [('bar', PrimitiveListCodec(int)), ('baz', PrimitiveListCodec(str))]),
            table('Qux', Qux, [('norf', PrimitiveListCodec(float))]))


def game_tables_codec(*table_codecs):
    return ComposedCodec(
        ZippedCodec(*table_codecs),
        DelimitedStringsCodec('\n\n', postfixed=True),
    )


class CodecTests(unittest.TestCase):
    def test_game_state_placements_are_components_indexed_by_entity(self):
        codec = GameStateCodec()
        path = Path(__file__).resolve().parents[1] / 'data/world.game'
        state = codec.decode(path.read_text(encoding='utf-8'))

        placements = state[8]
        self.assertEqual(set(placements), {'player'})
        self.assertIsInstance(placements['player'], ObjectPlacement)
        self.assertEqual(placements['player'].archetype, 'child')
        self.assertEqual(tuple(placements['player'].position), (8.5, 8.5, 0.5))

        decoded = codec.decode(codec.encode(state))
        self.assertEqual(decoded[8].keys(), placements.keys())
        self.assertEqual(decoded[8]['player'].archetype, placements['player'].archetype)
        self.assertEqual(tuple(decoded[8]['player'].position), tuple(placements['player'].position))

    def test_game_state_codec_composes_model_and_table_codecs(self):
        image = PpmImageCodec().decode('P3\n1 1\n255\n2 1 0\n')
        tiles = {'ground': TileArchetype('grass.png', 'ground.png')}
        map_ = MapCodec({1: 'ground'}, tiles).decode(image)
        archetypes = ArchetypeComponentStores(tiles=tiles)
        base = GameState(map_, {'old': 1}, archetypes)
        model = replace(
            base,
            globals={'quest': 2},
            inventory=defaultdict(int, {'apple': 3}),
            instances=InstanceComponentStores(
                placements={'player': ObjectPlacement('child', glm.vec3(.5, .5, 1))},
                physics={'player': VerticalPhysics(0, True)},
                characters={'player': CharacterAnimationState()},
            ),
        )

        codec = GameStateCodec()
        self.assertIsInstance(codec.encoder_sequence[0], PluginListCodec)
        decoded = codec.decode(codec.encode(PluginOps().save(model)))

        self.assertEqual(decoded[1], model.globals)
        self.assertEqual(decoded[2], model.inventory)
        self.assertEqual(decoded[9], model.instances.physics)
        self.assertEqual(decoded[10], model.instances.characters)
        self.assertEqual(decoded[8].keys(), model.instances.placements.keys())
        self.assertEqual(decoded[8]['player'].archetype, 'child')
        self.assertEqual(tuple(decoded[8]['player'].position), (.5, .5, 1))

    def test_composed_tables_round_trip(self):
        codec = game_tables_codec(*tables())
        content = [
            {'player': Foo(3, '  literal \\n and \\t\tactual tab\n\n# hash\r  '),
             '1': Foo(1, ''), 'integer': Foo(2, 'integer'), '(2, 3)': Foo(4, 'coordinate')},
            {'qux': Qux(1.25)},
        ]
        encoded = codec.encode(content)
        self.assertTrue(encoded.startswith('# Foo\n'))
        self.assertIn('\n\n# Qux\n', encoded)
        self.assertEqual(codec.decode(encoded), content)
        self.assertEqual(game_tables_codec(*tables()).encode(content), encoded)
        self.assertEqual(game_tables_codec(*tables()).decode(encoded + '\n'), content)

    def test_empty_tables_and_comments_round_trip(self):
        codec = game_tables_codec(*tables())
        self.assertEqual(codec.decode(codec.encode([{}, {}])), [{}, {}])
        encoded = codec.encode([{'player': Foo(1, '# literal hash')}, {}])
        encoded = encoded.replace('entity\tbar\tbaz\n', 'entity\tbar\tbaz\n# a comment\n')
        self.assertEqual(codec.decode(encoded)[0]['player'].baz, '# literal hash')

    def test_model_components_with_booleans_and_glm_vectors_round_trip(self):
        codec = game_tables_codec(
            table('Physics', VerticalPhysics,
                  [('vertical_velocity', PrimitiveListCodec(float)), ('is_grounded', PrimitiveListCodec(bool))]),
            table('Characters', CharacterAnimationState,
                  [('facing', ContainerListCodec(glm.vec2, float, 2)),
                   ('animation', PrimitiveListCodec(str)), ('elapsed', PrimitiveListCodec(float))]),
        )
        content = [{'player': VerticalPhysics(-1.25, True)},
                   {'player': CharacterAnimationState(glm.vec2(1, 0), 'standing', 0.25)}]
        self.assertEqual(codec.decode(codec.encode(content)), content)

    def test_invalid_tables_are_not_silently_truncated_or_reassigned(self):
        codec = game_tables_codec(*tables())
        encoded = codec.encode([{'player': Foo(1, 'text')}, {'qux': Qux(2)}])
        sections = encoded.split('\n\n')
        for invalid in (sections[0], encoded + '\n\n' + sections[0],
                        '\n\n'.join(reversed(sections)),
                        encoded.replace('entity\tbar\tbaz', 'entity\tbaz\tbar'),
                        encoded.replace('player\t1\ttext', 'player\t1'),
                        encoded.replace('player\t1\ttext', 'player\t1\ttext\nplayer\t2\tother')):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                codec.decode(invalid)
        with self.assertRaises(ValueError):
            codec.encode([{}])

    def test_text_escapes_preserve_literal_sequences_and_whitespace(self):
        codec = EscapedTextCodec()
        for text in ('', '\\', r'\n', r'\t\r', '\t\n\r', '\\\t', '  # apple  ', '村の子ども'):
            with self.subTest(text=text):
                self.assertEqual(codec.decode(codec.encode(text)), text)
        for invalid in ('\\', r'\q'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                codec.decode(invalid)


class MapCodecTests(unittest.TestCase):
    def test_ppm_channel_values_and_initial_placement(self):
        image = PpmImageCodec().decode('P3\n# channel comments\n2 1\n255\n4 1 0 12 1 7\n')
        tiles = {'grass': TileArchetype('grass.png', 'ground.png', max_erosion=1)}
        map_ = MapCodec({1: 'grass'}, tiles).decode(image)
        self.assertAlmostEqual(map_.height(glm.vec2(1.999, 0.5)), 5.999, places=5)
        placements = ObjectPlacementCodec({7: 'tree'}, map_).decode(image)
        self.assertEqual(len(placements), 1)
        self.assertEqual(set(placements), {'(1, 0)'})
        self.assertEqual(placements['(1, 0)'].archetype, 'tree')
        self.assertEqual(tuple(placements['(1, 0)'].position), (1.5, 0.5, 5.5))

    def test_canonical_map_loads_all_nonzero_object_pixels(self):
        with open(Path(__file__).resolve().parents[1] / 'data/world.ppm', encoding='ascii') as file:
            image = PpmImageCodec().decode(file.read())
        tiles = {'ground': TileArchetype('ground.png', 'ground.png', max_erosion=1)}
        map_ = MapCodec({1: 'ground', 2: 'ground', 3: 'ground'}, tiles).decode(image)
        placements = ObjectPlacementCodec({index: str(index) for index in range(1, 6)}, map_).decode(image)
        self.assertEqual(tuple(map_.dimensions), (18, 18))
        self.assertEqual(len(placements), sum(blue != 0 for _, _, blue in image.pixels))
        self.assertGreater(len(placements), 0)
        for placement in placements.values():
            self.assertEqual(placement.position.z, map_.height(glm.vec2(placement.position)))

    def test_bad_ppm_and_missing_palette_entries_are_rejected(self):
        codec = PpmImageCodec()
        for invalid in ('P6 1 1 255 0 0 0', 'P3 0 1 255', 'P3 1 1 255 0 0', 'P3 1 1 255 256 1 0'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                codec.decode(invalid)
        image = codec.decode('P3 1 1 255 4 1 7')
        tiles = {'ground': TileArchetype('ground.png', 'ground.png')}
        with self.assertRaises(ValueError):
            MapCodec({}, tiles).decode(image)
        map_ = MapCodec({1: 'ground'}, tiles).decode(image)
        with self.assertRaises(ValueError):
            ObjectPlacementCodec({}, map_).decode(image)
