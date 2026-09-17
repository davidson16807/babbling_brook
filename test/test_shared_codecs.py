import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from pyglm import glm

from babbling_brook.codec import BabblingBrookFileCodec, GameTablesCodec
from babbling_brook.model import Plugin, PluginOps
from babbling_brook.model.GameFiles import GameFiles
from babbling_brook.model.component.instances import CharacterAnimationState
from babbling_brook.view.view.BillboardView import BillboardView
from babbling_brook.view.program.ViewState import ViewState

ROOT = Path(__file__).parents[1]


class CodecTests(unittest.TestCase):
    def test_supplied_world_round_trip_and_named_section_order(self):
        codec = BabblingBrookFileCodec()
        original = (ROOT / 'data/world.game').read_text()
        plugin = codec.decode(original)
        self.assertEqual(plugin, codec.decode(codec.encode(plugin)))
        tables = GameTablesCodec().decode(original)
        reordered = GameTablesCodec().encode(dict(reversed(tuple(tables.items()))))
        self.assertEqual(plugin, codec.decode(reordered))
        self.assertEqual(len(plugin.objects), 6)
        self.assertEqual(len(plugin.animation_frames), 24)

    def test_sparse_overlay_and_unknown_sections(self):
        codec = BabblingBrookFileCodec()
        self.assertEqual(codec.decode('# globals\nkey\tvalue\nwind\t2.5\n'), Plugin(globals={'wind': 2.5}))
        generic = GameTablesCodec()
        text = '# future_rules\nkey\tvalue\nspecial\tyes\n'
        tables = generic.decode(text)
        self.assertEqual(generic.decode(generic.encode(tables)), tables)
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            codec.decode(text)

    def test_literal_hashes_whitespace_and_escapes_survive(self):
        codec = BabblingBrookFileCodec()
        plugin = codec.decode((ROOT / 'data/world.game').read_text())
        label = '  #1\tline\nnext\rline \\t \\n \\  '
        plugin = replace(plugin, objects={'apple': replace(plugin.objects['apple'], label=label)})
        self.assertEqual(codec.decode(codec.encode(plugin)), plugin)

    def test_bad_sections_columns_duplicate_ids_and_versions_are_rejected(self):
        codec = BabblingBrookFileCodec()
        for text in (
            '# globals\nkey\tvalue\na\t1\n\n# globals\nkey\tvalue\n',
            '# globals\nkey\tkey\na\t1\n',
            '# globals\nkey\tvalue\na\t1\textra\n',
            '# globals\nkey\tvalue\na\t1\na\t2\n',
            '# globals\nwrong\tvalue\na\t1\n',
            '# format\nkey\tvalue\nversion\t2\n',
            '# globals\nkey\tvalue\na\t\\q\n',
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                codec.decode(text)

    def test_legacy_uncommented_object_header_is_read(self):
        text = (ROOT / 'data/world.game').read_text().replace('# archetype\ttexture', 'archetype\ttexture')
        self.assertIn('apple', BabblingBrookFileCodec().decode(text).objects)


class SharedStateTests(unittest.TestCase):
    def setUp(self):
        self.codec = BabblingBrookFileCodec()
        self.ops = PluginOps()
        self.files = GameFiles(self.ops, self.codec)
        self.map_, self.plugin = self.files.load_content(ROOT / 'data/world.ppm', [ROOT / 'data/world.game'])

    def test_named_animations_load_save_and_draw_with_standing_fallback(self):
        frames = dict(self.plugin.animation_frames)
        for name in ('attacking', 'disabled', 'cooldown', 'custom_pose'):
            frames.update({('child', name, direction, frame): (f'{name}-{direction}-{frame}.svg', .2)
                           for direction in (0, 1) for frame in (0, 1)})
        state = self.ops.load(self.map_, replace(self.plugin, animation_frames=frames))
        saved = self.codec.decode(self.codec.encode(self.ops.save(state)))
        restored = self.ops.load(self.map_, saved)
        self.assertEqual(saved.animation_frames, frames)
        self.assertEqual(restored.archetypes.characters, state.archetypes.characters)
        for name, expected in (('cooldown', 'cooldown-0-1.svg'), ('missing', 'child-front-0.svg')):
            class Program:
                calls = []
                def draw(self, *args):
                    self.calls.append(args)
            program = Program()
            instances = replace(state.instances,
                placements={'player': state.instances.placements['player']},
                characters={'player': CharacterAnimationState(glm.vec2(-1, -1), name, .25)})
            BillboardView(program).draw(SimpleNamespace(forward=lambda: glm.vec3(0, 1, -1)), instances, state.archetypes,
                                        ViewState(glm.mat4(1), glm.vec3(1, 0, 0)))
            self.assertEqual(program.calls[0][0], expected)
            self.assertEqual(program.calls[0][4], (False,))

    def test_incomplete_or_invalid_animation_frames_raise_value_error(self):
        for change in ('missing', 'duration', 'no_standing'):
            frames = dict(self.plugin.animation_frames)
            if change == 'missing':
                del frames['child', 'walking', 0, 1]
            elif change == 'duration':
                frames['child', 'walking', 0, 1] = ('frame.svg', 0)
            else:
                frames = {key: value for key, value in frames.items() if key[0:2] != ('child', 'standing')}
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.ops.load(self.map_, replace(self.plugin, animation_frames=frames))

    def test_save_restores_snapshot_without_respawning_base_or_map_objects(self):
        state = self.ops.load(self.map_, self.plugin)
        state.inventory['apple'] = 3
        instances = replace(state.instances,
                            placements={'player': replace(state.instances.placements['player'], position=glm.vec3(3.5, 3.5, 5))},
                            physics={}, characters={'player': CharacterAnimationState(animation='walking', elapsed=.4)})
        state = replace(state, instances=instances)
        with tempfile.TemporaryDirectory() as directory:
            save = Path(directory) / 'slot.sav'
            self.files.save(save, state)
            restored = self.files.load(ROOT / 'data/world.ppm', [ROOT / 'data/world.game'], save)
        self.assertEqual(restored.instances.placements, instances.placements)
        self.assertEqual(restored.inventory['apple'], 3)
        self.assertEqual(restored.instances.characters, instances.characters)
        # Explicitly remove an object supplied by the base .game, too.
        empty = replace(state, instances=replace(instances, placements={}, characters={}))
        with tempfile.TemporaryDirectory() as directory:
            save = Path(directory) / 'slot.sav'
            self.files.save(save, empty)
            restored = self.files.load(ROOT / 'data/world.ppm', [ROOT / 'data/world.game'], save)
        self.assertEqual(restored.instances.placements, {})

    def test_failed_save_preserves_existing_file(self):
        state = self.ops.load(self.map_, self.plugin)
        with tempfile.TemporaryDirectory() as directory:
            save = Path(directory) / 'slot.sav'
            save.write_text('previous save')
            with patch('babbling_brook.model.GameFiles.os.replace', side_effect=OSError('failure')):
                with self.assertRaises(OSError):
                    self.files.save(save, state)
            self.assertEqual(save.read_text(), 'previous save')
            self.assertFalse(save.with_name('slot.sav.tmp').exists())
