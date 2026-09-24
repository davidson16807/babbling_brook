from math import pi
from pathlib import Path
import unittest

from pyglm import glm

from babbling_brook.codec.GameStateCodec import PluginStringCodec
from babbling_brook.messages import KeyboardAction, KeyboardMessage, MouseButton, MouseMotionMessage
from babbling_brook.model.GameFiles import GameFiles
from babbling_brook.model.plugin.PluginOps import PluginOps
from babbling_brook.update.DirectionalKeysUpdater import DirectionalKeysUpdater
from babbling_brook.update.GameUpdater import GameUpdater
from babbling_brook.update.HemisphereLookUpdater import HemisphereLookUpdater


class CameraInputTests(unittest.TestCase):
    def test_directional_speed_scales_each_axis_and_opposing_keys_cancel(self):
        updater = DirectionalKeysUpdater(*'ijkl', glm.vec2(.5, .25))
        self.assertEqual(updater.update(frozenset('il')), glm.vec2(.5, .25))
        self.assertEqual(updater.update(frozenset('jk')), glm.vec2(-.5, -.25))
        self.assertEqual(updater.update(frozenset('ijkl')), glm.vec2(0))
        self.assertEqual(updater.update(frozenset('wasd')), glm.vec2(0))

    def test_mouse_updater_returns_angle_delta_without_snapping(self):
        updater = HemisphereLookUpdater()
        result = updater.update(MouseMotionMessage(glm.vec2(10), glm.vec2(13, -7)))
        self.assertAlmostEqual(result.x, -.13)
        self.assertAlmostEqual(result.y, .07)
        self.assertEqual(updater.update(KeyboardMessage('i', KeyboardAction.PRESS)), glm.vec2(0))

    def test_game_accumulates_small_drags_before_snapping_and_keys_turn_90_degrees(self):
        data = Path(__file__).resolve().parents[1] / 'data'
        game = GameFiles(PluginOps(), PluginStringCodec()).load(data / 'world.ppm', [data / 'world.game'])
        updater = GameUpdater(HemisphereLookUpdater(),
                              DirectionalKeysUpdater(*'ijkl', glm.vec2(pi / 2, pi / 6)),
                              None, None)
        drag = MouseMotionMessage(glm.vec2(0), glm.vec2(-1, 0), frozenset((MouseButton.MIDDLE,)))
        first = updater.update(game, drag)
        self.assertAlmostEqual(first.camera.azimuth, pi / 4)
        self.assertAlmostEqual(first.camera_drag_remainder, .01)
        for _ in range(80):
            game = updater.update(game, drag)
        self.assertAlmostEqual(game.camera.azimuth, 3 * pi / 4)
        turned = updater.update(game, KeyboardMessage('l', KeyboardAction.PRESS))
        self.assertAlmostEqual(turned.camera.azimuth, 5 * pi / 4)
        restored = updater.update(turned, KeyboardMessage('j', KeyboardAction.PRESS))
        self.assertAlmostEqual(restored.camera.azimuth, game.camera.azimuth)
        for _ in range(4):
            restored = updater.update(restored, KeyboardMessage('l', KeyboardAction.PRESS))
        self.assertAlmostEqual(restored.camera.azimuth, game.camera.azimuth)
        tilted = updater.update(game, KeyboardMessage('i', KeyboardAction.PRESS))
        self.assertAlmostEqual(tilted.camera.elevation, pi / 3)


if __name__ == '__main__':
    unittest.main()
