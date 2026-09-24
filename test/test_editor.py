from dataclasses import replace
from math import pi, sin
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pyglm import glm

from babbling_brook.codec.map.PpmImageCodec import PpmImage, PpmImageCodec
from babbling_brook.messages import (KeyboardAction, KeyboardMessage, KeyboardModifiers,
                                     MouseButton, MouseMotionMessage, ScrollMessage)
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
        self.updater = EditorUpdater(DirectionalKeysUpdater(*'wasd', glm.vec2(1)),
                                     DirectionalKeysUpdater(*'ijkl', glm.vec2(pi / 4)),
                                     HemisphereLookUpdater())

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

    def test_brackets_and_parentheses_edit_ids(self):
        tile = self.updater.update(self.state, self.key(']'))
        object_ = self.updater.update(self.state, self.key('0', KeyboardModifiers.SHIFT))
        self.assertEqual(tile.image.pixels[4], (2, 8, 3))
        self.assertEqual(self.updater.update(tile, self.key('[')).image, self.image)
        self.assertEqual(object_.image.pixels[4], (2, 7, 4))
        self.assertEqual(self.updater.update(self.state, self.key(')')).image, object_.image)
        self.assertEqual(self.updater.update(self.state, self.key('0')).image, self.image)
        self.state = self.updater.update(self.state, self.key('9', KeyboardModifiers.SHIFT))
        for _ in range(2):
            self.state = self.updater.update(self.state, self.key('('))
        self.assertEqual(self.state.image.pixels[4][2], 0)
        self.assertNotIn('(1, 1)', self.state.placements)

    def test_height_controls_ignore_modifiers(self):
        for modifiers in (KeyboardModifiers.NONE, KeyboardModifiers.SHIFT, KeyboardModifiers.CTRL,
                          KeyboardModifiers.SHIFT | KeyboardModifiers.CTRL):
            for message in (self.key('>', modifiers), ScrollMessage(glm.vec2(0, 1), modifiers)):
                with self.subTest(message=message):
                    result = self.updater.update(self.state, message)
                    self.assertEqual(result.image.pixels[4], (3, 7, 3))

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
        self.assertEqual(self.state.cursor, [(1, 1)])
        corner = replace(self.state, cursor=[(0, 0)])
        self.assertEqual(self.updater.update(corner, self.key('w')).cursor, [(0, 0)])
        moved = self.updater.update(corner, self.key('d'))
        self.assertEqual(moved.cursor, [(0, 1)])
        self.assertEqual(self.updater.step(moved, .05, frozenset('d')).cursor, [(0, 1)])
        self.assertEqual(self.updater.step(moved, .3, frozenset('d')).cursor, [(0, 2)])
        turned = self.updater.update(self.state, self.key('l'))
        self.assertAlmostEqual(turned.camera.azimuth, pi / 2)
        self.assertEqual(self.updater.update(turned, self.key('w')).cursor, [(1, 0)])

    def test_shift_selects_rectangle_and_can_shrink_back_to_anchor(self):
        shift = KeyboardModifiers.SHIFT
        selected = self.updater.update(self.state, self.key('w', shift))
        selected = self.updater.update(selected, self.key('d', shift))
        self.assertEqual(selected.cursor[0], (1, 1))
        self.assertEqual(selected.cursor[-1], (0, 2))
        self.assertCountEqual(selected.cursor, [(1, 1), (0, 1), (1, 2), (0, 2)])
        self.assertEqual(self.state.cursor, [(1, 1)])
        released = self.updater.update(selected, KeyboardMessage('shift', KeyboardAction.RELEASE))
        self.assertEqual(self.updater.step(released, .3, frozenset()).cursor, selected.cursor)
        shrunk = self.updater.update(selected, self.key('a', shift))
        self.assertEqual(shrunk.cursor, [(1, 1), (0, 1)])
        self.assertEqual(self.updater.update(shrunk, self.key('s', shift)).cursor, [(1, 1)])
        self.assertEqual(self.updater.update(selected, self.key('s')).cursor, [(1, 2)])

    def test_held_shift_extends_selection_and_group_edits_undo_together(self):
        start = replace(self.state, cursor=[(0, 0)])
        for shift in ('shift', 'right shift'):
            with self.subTest(shift=shift):
                selected = self.updater.update(start, self.key('d', KeyboardModifiers.SHIFT))
                selected = self.updater.step(selected, .3, frozenset(('d', shift)))
                self.assertEqual(selected.cursor, [(0, 0), (0, 1), (0, 2)])
                for key, channel, value in (('.', 0, 3), (']', 1, 8), (')', 2, 1)):
                    edited = self.updater.update(selected, self.key(key))
                    for index in (0, 3, 6):
                        self.assertEqual(edited.image.pixels[index][channel], value)
                    self.assertEqual(edited.image.pixels[4], self.image.pixels[4])
                    self.assertEqual(len(edited.undo), 1)
                    undone = self.updater.update(edited, self.key('z', KeyboardModifiers.CTRL))
                    self.assertEqual(undone.image, self.image)
                    self.assertEqual(undone.cursor, selected.cursor)

    def test_camera_has_45_degree_keys_continuous_drag_and_range_limits(self):
        for key, daz, del_ in (('i', 0, pi / 4), ('k', 0, -pi / 4),
                              ('j', -pi / 4, 0), ('l', pi / 4, 0)):
            result = self.updater.update(self.state, self.key(key))
            self.assertAlmostEqual(result.camera.azimuth, max(0, pi / 4 + daz))
            self.assertAlmostEqual(result.camera.elevation, max(0, pi / 6 + del_))
        buttons = frozenset((MouseButton.MIDDLE,))
        dragged = self.updater.update(self.state, MouseMotionMessage(glm.vec2(0), glm.vec2(-13, -7), buttons))
        self.assertAlmostEqual(dragged.camera.azimuth, pi / 4 + .13)
        self.assertAlmostEqual(dragged.camera.elevation, pi / 6 + .07)
        self.assertAlmostEqual(dragged.camera.right().x, -sin(pi / 4 + .13))
        for offset, expected in ((-1000, (pi, pi / 2)), (1000, (0, 0))):
            clamped = self.updater.update(dragged, MouseMotionMessage(glm.vec2(0), glm.vec2(offset), buttons))
            self.assertEqual((clamped.camera.azimuth, clamped.camera.elevation), expected)
        untouched = self.updater.update(self.state, MouseMotionMessage(glm.vec2(0), glm.vec2(100)))
        self.assertIs(untouched, self.state)

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
        self.assertEqual(result.image.pixels[4], (1, 7, 3))

    def test_unsaved_exit_requires_second_request(self):
        changed = self.updater.update(self.state, self.key('.'))
        pending = self.updater.update(changed, self.key('escape'))
        self.assertTrue(pending.running)
        self.assertTrue(pending.quit_pending)
        self.assertFalse(self.updater.update(pending, self.key('escape')).running)


if __name__ == '__main__':
    unittest.main()
