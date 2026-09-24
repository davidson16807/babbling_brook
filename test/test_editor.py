from dataclasses import replace
from math import pi
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pyglm import glm

from babbling_brook.codec.map.PpmImageCodec import PpmImage, PpmImageCodec
from babbling_brook.messages import KeyboardAction, KeyboardMessage, KeyboardModifiers, ScrollMessage
from babbling_brook.model.EditorFiles import EditorFiles
from babbling_brook.update.DirectionalKeysUpdater import DirectionalKeysUpdater
from babbling_brook.update.EditorUpdater import EditorUpdater
from babbling_brook.update.HemisphereLookUpdater import HemisphereLookUpdater

ROOT = Path(__file__).resolve().parents[1]


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'level.ppm'
        pixels = [(2, 7, 0)] * 9
        pixels[4] = (2, 7, 3)
        self.image = PpmImage(3, 3, 16, tuple(pixels))
        self.path.write_text(PpmImageCodec().encode(self.image), encoding='ascii')
        self.files = EditorFiles(ROOT / 'data')
        self.state = self.files.load(self.path)
        self.updater = EditorUpdater(DirectionalKeysUpdater(*'wasd'),
                                     DirectionalKeysUpdater(*'ijkl'), HemisphereLookUpdater())

    def key(self, key, modifiers=KeyboardModifiers.NONE):
        return KeyboardMessage(key, KeyboardAction.PRESS, modifiers)

    def test_height_edit_moves_object_base_and_preserves_other_cells(self):
        result = self.updater.update(self.state, self.key('.'))
        self.assertEqual(result.image.pixels[4], (3, 7, 3))
        self.assertEqual(result.image.pixels[:4], self.image.pixels[:4])
        self.assertEqual(result.image.pixels[5:], self.image.pixels[5:])
        self.assertEqual(result.map.height(glm.vec2(1.5, 1.5)), 1.5)
        self.assertEqual(result.placements['(1, 1)'].position.z, 1.5)
        self.assertNotIn('player', result.placements)
        self.assertEqual(self.state.image, self.image)

    def test_modifiers_edit_separate_channels(self):
        tile = self.updater.update(self.state, self.key('.', KeyboardModifiers.CTRL))
        object_ = self.updater.update(self.state, ScrollMessage(glm.vec2(0, 1), KeyboardModifiers.SHIFT))
        self.assertEqual(tile.image.pixels[4], (2, 8, 3))
        self.assertEqual(object_.image.pixels[4], (2, 7, 4))
        for _ in range(3):
            self.state = self.updater.update(self.state, self.key(',', KeyboardModifiers.SHIFT))
        self.assertEqual(self.state.image.pixels[4][2], 0)
        self.assertNotIn('(1, 1)', self.state.placements)

    def test_undo_redo_and_atomic_save(self):
        changed = self.updater.update(self.state, self.key('.'))
        undone = self.updater.update(changed, self.key('z', KeyboardModifiers.CTRL))
        self.assertFalse(undone.dirty)
        redone = self.updater.update(undone, self.key('y', KeyboardModifiers.CTRL))
        original = self.path.read_bytes()
        with patch('babbling_brook.model.EditorFiles.os.replace', side_effect=OSError('blocked')):
            with self.assertRaises(OSError):
                self.files.save(redone)
        self.assertEqual(self.path.read_bytes(), original)
        saved = self.files.save(redone)
        self.assertFalse(saved.dirty)
        self.assertEqual(PpmImageCodec().decode(self.path.read_text()), redone.image)
        self.assertEqual(self.files.load(self.path).image, saved.image)

    def test_cursor_bounds_camera_and_repeat_delay(self):
        corner = replace(self.state, cursor=(0, 0))
        self.assertEqual(self.updater.update(corner, self.key('w')).cursor, (0, 0))
        moved = self.updater.update(corner, self.key('d'))
        self.assertEqual(moved.cursor, (0, 1))
        self.assertEqual(self.updater.step(moved, .05, frozenset('d')).cursor, (0, 1))
        self.assertEqual(self.updater.step(moved, .3, frozenset('d')).cursor, (0, 2))
        turned = self.updater.update(self.state, self.key('l'))
        self.assertAlmostEqual(turned.camera.look_azimuth(), 3 * pi / 4)
        self.assertEqual(self.updater.update(turned, self.key('w')).cursor, (1, 0))

    def test_maxval_can_grow_without_rescaling(self):
        raised = replace(self.image, maximum=2, pixels=((2, 0, 0),) * 9)
        self.path.write_text(PpmImageCodec().encode(raised))
        state = self.updater.update(self.files.load(self.path), self.key('.'))
        self.assertEqual(state.image.maximum, 3)
        self.assertEqual(state.image.pixels[0], (2, 0, 0))
        image16 = PpmImage(1, 1, 65535, ((65535, 32768, 1),))
        self.assertEqual(PpmImageCodec().decode(PpmImageCodec().encode(image16)), image16)

    def test_height_edit_rebuilds_neighbor_erosion(self):
        image = replace(self.image, pixels=((4, 3, 0),) * 9)
        self.path.write_text(PpmImageCodec().encode(image))
        state = self.files.load(self.path)
        before = state.map.corner_heights((0, 0))
        lowered = self.updater.update(state, self.key(','))
        self.assertNotEqual(lowered.map.corner_heights((0, 0)), before)

    def test_scroll_adapter_preserves_modifier_sample(self):
        try:
            import pygame
            from babbling_brook.adapter.PygameMessageQueue import PygameMessageQueue
        except ImportError:
            self.skipTest('Pygame is not installed')
        event = pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=-1)
        with patch.object(pygame.key, 'get_mods', return_value=pygame.KMOD_CTRL):
            message, = PygameMessageQueue(events=lambda: (event,)).poll()
        self.assertEqual(message.modifiers, KeyboardModifiers.CTRL)
        result = self.updater.update(self.state, message)
        self.assertEqual(result.image.pixels[4], (2, 6, 3))

    def test_unsaved_exit_requires_second_request(self):
        changed = self.updater.update(self.state, self.key('.'))
        pending = self.updater.update(changed, self.key('escape'))
        self.assertTrue(pending.running)
        self.assertTrue(pending.quit_pending)
        self.assertFalse(self.updater.update(pending, self.key('escape')).running)


if __name__ == '__main__':
    unittest.main()
