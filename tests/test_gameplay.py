import unittest
from bootstrap import ROOT
try:
    from pyglm import glm
except ImportError:
    raise unittest.SkipTest('PyGLM is required for model and gameplay tests')
from collections import defaultdict
from dataclasses import replace
from math import pi
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from babbling_brook.game import load_game, save_game, save_sections, codec
from babbling_brook.model.Map import Map
from babbling_brook.model.Field import Field
from babbling_brook.model.components.archetypes import TileArchetype, ObjectArchetype
from babbling_brook.model.components.instances import VerticalPhysics
from babbling_brook.model.systems.CollisionSystem import CollisionSystem
from babbling_brook.model.systems.GravitySystem import GravitySystem
from babbling_brook.update.GameUpdater import default_updater
from babbling_brook.messages import (KeyboardMessage, KeyboardAction, TickMessage, MouseButtonMessage,
    ButtonAction, MouseButton, MouseMotionMessage, FocusLostMessage)


def terrain(width, height, heights, ids=None, tiles=None):
    dimensions = glm.ivec2(width, height)
    return Map(dimensions, Field(dimensions, tuple(heights)), Field(dimensions, tuple(ids or ['flat'] * (width * height))),
               tiles or {'flat': TileArchetype('stone.png', 'stone.png')})


def press(key):
    return KeyboardMessage(key, KeyboardAction.PRESS)


class TerrainTests(unittest.TestCase):

    def test_rendered_triangles_match_collision(self):
        from babbling_brook.view.views.TileView import TileView
        tiles = {'e': TileArchetype('grass.png', 'stone.png', max_erosion=1)}
        map_ = terrain(2, 2, [3, 2, 1, 4], ['e'] * 4, tiles)
        coordinates, heights = TileView(None)._build(map_)['grass.png', 'stone.png']
        self.assertEqual(len(coordinates), 4)
        for coordinate, height in zip(coordinates, heights):
            x, y = coordinate
            corners = (
                glm.vec3(x, y, height[0][0]),
                glm.vec3(x + 1, y, height[1][0]),
                glm.vec3(x, y + 1, height[0][1]),
                glm.vec3(x + 1, y + 1, height[1][1]),
            )
            for indices in ((0, 1, 3), (0, 3, 2)):
                center = sum((corners[index] for index in indices), glm.vec3(0)) / 3
                self.assertAlmostEqual(map_.height(glm.vec2(center)), center.z, places=5)

    def test_field_rejects_wrong_size(self):
        with self.assertRaises(ValueError):
            Field(glm.ivec2(2, 2), (1,))


class GameplayTests(unittest.TestCase):
    def setUp(self):
        self.model = load_game(ROOT / 'data')
        self.updater = default_updater()

    def test_initial_map_placement_and_pickup(self):
        self.assertTrue(self.model.map.static_objects)
        self.assertIn('player', self.model.instances.characters)
        before = self.model
        after = self.updater.update(before, press('e'))
        self.assertIsInstance(after.inventory, defaultdict)
        self.assertEqual(after.inventory['apple'], 1)
        self.assertEqual(before.inventory, {})
        self.assertEqual(len(after.instances.positionables), len(before.instances.positionables) - 1)
        self.assertTrue(self.updater.update(after, press('tab')).show_inventory)

    def test_movement_relative_to_four_camera_azimuths(self):
        for angle in (pi/4, 3*pi/4, 5*pi/4, 7*pi/4):
            model = replace(self.model, camera=replace(self.model.camera, look_azimuth=angle))
            before = glm.vec3(model.instances.positionables['player'])
            model = self.updater.update(self.updater.update(model, press('w')), TickMessage(.05))
            from math import cos, sin
            delta = glm.vec2(model.instances.positionables['player'] - before)
            self.assertGreater(glm.dot(delta, glm.vec2(-cos(angle), -sin(angle))), .1)

    def test_jump_has_no_double_jump_and_lands(self):
        model = self.updater.update(self.model, press('space'))
        model = self.updater.update(model, TickMessage(.1))
        self.assertGreater(model.instances.positionables['player'].z, .5)
        velocity = model.instances.physics['player'].vertical_velocity
        model = self.updater.update(model, press('space'))
        self.assertEqual(model.instances.physics['player'].vertical_velocity, velocity)
        for _ in range(120):
            model = self.updater.update(model, TickMessage(1/120))
        self.assertTrue(model.instances.physics['player'].is_grounded)
        self.assertAlmostEqual(model.instances.positionables['player'].z, .5)

    def test_camera_drag_and_focus_loss(self):
        model = self.updater.update(self.model, MouseButtonMessage(MouseButton.MIDDLE, ButtonAction.PRESS, 0))
        for _ in range(100):
            model = self.updater.update(model, MouseMotionMessage(glm.vec2(0), glm.vec2(1, 0)))
        self.assertNotEqual(model.camera.look_azimuth, self.model.camera.look_azimuth)
        self.assertEqual(model.camera.elevation, self.model.camera.elevation)
        model = self.updater.update(self.updater.update(model, press('w')), FocusLostMessage())
        self.assertFalse(model.controls.pressed_keys)
        self.assertFalse(model.controls.pressed_mouse_buttons)

    def test_save_restores_every_object_and_midair_physics(self):
        model = self.updater.update(self.model, press('e'))
        model = self.updater.update(self.updater.update(model, press('space')), TickMessage(.1))
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'slot.sav'
            save_game(path, model)
            with patch('babbling_brook.game.ObjectPlacementCodec.decode', side_effect=AssertionError('Map objects respawned')):
                restored = load_game(ROOT / 'data', path)
            self.assertEqual(save_sections(restored), save_sections(model))
            self.assertIsInstance(restored.inventory, defaultdict)
            self.assertFalse(path.with_name('slot.sav.tmp').exists())

    def test_failed_save_preserves_previous_file(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'slot.sav'
            save_game(path, self.model)
            previous = path.read_bytes()
            with patch('babbling_brook.game.os.replace', side_effect=OSError('interrupted')):
                with self.assertRaises(OSError):
                    save_game(path, self.updater.update(self.model, press('e')))
            self.assertEqual(path.read_bytes(), previous)

    def test_duplicate_saved_objects_rejected(self):
        sections = save_sections(self.model)
        sections['objects'].append(sections['objects'][1])
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'slot.sav'
            path.write_text(codec.encode(sections))
            with self.assertRaises(ValueError):
                load_game(ROOT / 'data', path)

    def test_object_collision_and_platform_landing(self):
        map_ = terrain(3, 1, [0, 1, 1])
        objects = {'child': ObjectArchetype('child.png'), 'rock': ObjectArchetype('rock.png')}
        collision = CollisionSystem()
        positions = {'player': glm.vec3(.7, .5, 0), 'rock': glm.vec3(.9, .5, 0)}
        ids = {'player': 'child', 'rock': 'rock'}
        blocked = collision.move('player', positions['player'], glm.vec2(.05, 0), positions, ids, objects, {}, map_)
        self.assertEqual(blocked, positions['player'])
        # The ledge blocks walking; jumping above it allows crossing and landing.
        positions = {'player': glm.vec3(.99, .5, 0)}
        ids = {'player': 'child'}
        blocked = collision.move('player', positions['player'], glm.vec2(.05, 0), positions, ids, objects, {}, map_)
        self.assertLess(blocked.x, 1)
        positions['player'] = glm.vec3(.99, .5, 1.1)
        crossed = collision.move('player', positions['player'], glm.vec2(.05, 0), positions, ids, objects, {}, map_)
        self.assertGreater(crossed.x, 1)
        positions, physics = {'player': crossed}, {'player': VerticalPhysics(-1, False)}
        for _ in range(30):
            positions, physics = GravitySystem().step(positions, physics, map_, 1/120)
        self.assertAlmostEqual(positions['player'].z, 1)
        self.assertTrue(physics['player'].is_grounded)


if __name__ == '__main__':
    unittest.main()
