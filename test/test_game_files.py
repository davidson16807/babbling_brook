import tempfile
import unittest
from pathlib import Path

from babbling_brook.codec import PluginStringCodec
from babbling_brook.model.GameFiles import GameFiles
from babbling_brook.model import Plugin, PluginOps


class RecordingPluginOps:
    def __init__(self):
        self.delegate = PluginOps()
        self.updated = []
        self.loaded = []
        self.saved = []

    def update(self, *plugins):
        self.updated.append(plugins)
        return self.delegate.update(*plugins)

    def load(self, map_, plugin):
        self.loaded.append((map_, plugin))
        return self.delegate.load(map_, plugin)

    def save(self, state):
        self.saved.append(state)
        return self.delegate.save(state)


class RecordingCodec:
    def __init__(self):
        self.delegate = PluginStringCodec()
        self.decoded = []
        self.encoded = []

    def decode(self, text):
        self.decoded.append(text)
        return self.delegate.decode(text)

    def encode(self, plugin):
        self.encoded.append(plugin)
        return self.delegate.encode(plugin)


class GameFilesTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parents[1]
        self.game_filename = self.root / 'data' / 'world.game'
        self.map_filename = self.root / 'data' / 'world.ppm'
        self.ops = RecordingPluginOps()
        self.codec = RecordingCodec()
        self.files = GameFiles(self.ops, self.codec)

    def test_load_uses_injected_dependencies_and_overlays_files_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            mod_filename = Path(directory) / 'weather.mod'
            mod_filename.write_text(
                self.codec.delegate.encode(Plugin(globals={'wind': 2.5})) + '\n',
                encoding='utf-8',
            )

            state = self.files.load(
                self.map_filename,
                [self.game_filename, mod_filename],
            )

        self.assertEqual(state.globals['wind'], 2.5)
        self.assertEqual(len(self.codec.decoded), 2)
        self.assertEqual(len(self.ops.updated), 2)
        self.assertEqual(len(self.ops.loaded), 1)

    def test_save_uses_injected_plugin_ops_and_codec(self):
        state = self.files.load(self.map_filename, [self.game_filename])

        with tempfile.TemporaryDirectory() as directory:
            save_filename = Path(directory) / 'slot.sav'
            self.files.save(save_filename, state)
            saved = self.codec.delegate.decode(save_filename.read_text(encoding='utf-8'))

        self.assertEqual(self.ops.saved, [state])
        self.assertEqual(self.codec.encoded, [saved])
        self.assertIn('player', saved.placements)

    def test_optional_save_file_is_applied_after_game_files(self):
        # Generate the fixture: personal save slots are not part of the archive.
        with tempfile.TemporaryDirectory() as directory:
            save_filename = Path(directory) / 'slot.sav'
            initial = GameFiles(PluginOps(), PluginStringCodec()).load(
                self.map_filename, [self.game_filename])
            initial.inventory['apple'] = 1
            save_filename.write_text(PluginStringCodec().encode(PluginOps().save(initial)), encoding='utf-8')
            state = self.files.load(self.map_filename, [self.game_filename], save_filename)

        self.assertEqual(state.inventory['apple'], 1)
        self.assertEqual(len(self.codec.decoded), 2)
        self.assertEqual(len(self.ops.updated), 2)

    def test_load_requires_at_least_one_game_file(self):
        with self.assertRaises(ValueError):
            self.files.load(self.map_filename, [])


class PluginOpsTests(unittest.TestCase):
    def test_methods_are_bound_to_an_instance(self):
        plugin_ops = PluginOps()
        self.assertIs(plugin_ops.update.__self__, plugin_ops)


if __name__ == '__main__':
    unittest.main()
