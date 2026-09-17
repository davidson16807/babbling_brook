import math
import unittest
from dataclasses import replace

from pyglm import glm

from babbling_brook.model.MotionSegment import MotionSegment, arc_height, linear_height
from babbling_brook.model.component.instances import Motion, ObjectPlacement
from babbling_brook.model.component.archetypes import ObjectArchetype
from babbling_brook.model.system.MotionSystem import MotionSystem
from babbling_brook.model.query.TileMotionQuery import TileMotionQuery
from babbling_brook.model.query.LineOfSightQuery import LineOfSightQuery
from test_models import terrain


class MotionTests(unittest.TestCase):
    def test_arc_endpoints_and_true_maximum_including_degenerate_cases(self):
        for start, end, maximum in ((2, 4, 7), (4, 2, 4), (2, 4, 4), (2, 2, 2), (-4, -2, 0)):
            with self.subTest(heights=(start, end, maximum)):
                a, b, c = arc_height(start, end, maximum, 2)
                self.assertAlmostEqual(c, start)
                self.assertAlmostEqual(4*a + 2*b + c, end)
                peak_time = -b / (2*a) if a else 0
                self.assertGreaterEqual(peak_time, 0)
                self.assertLessEqual(peak_time, 2)
                self.assertAlmostEqual(a*peak_time**2 + b*peak_time + c, maximum)
        with self.assertRaises(ValueError):
            arc_height(2, 4, 3, 1)

    def test_segment_is_raw_function_of_time(self):
        segment = MotionSegment(glm.vec2(.5, .5), glm.vec2(2.5, .5), linear_height(1, 3, 2), 2)
        self.assertEqual(tuple(segment(0)), (.5, .5, 1))
        self.assertEqual(tuple(segment(1)), (1.5, .5, 2))
        self.assertEqual(tuple(segment(2)), (2.5, .5, 3))

    def test_system_handles_multiple_segments_completion_and_terrain_clamping(self):
        map_ = terrain(3, [0, 2, 0], erosion=0)
        first = MotionSegment(glm.vec2(.5, .5), glm.vec2(1.5, .5), (0, 0, 0), .5)
        second = MotionSegment(glm.vec2(1.5, .5), glm.vec2(2.5, .5), (0, 0, 0), 1)
        placements = {'unit': ObjectPlacement('unit', glm.vec3(.5, .5, 0))}
        motions = {'unit': Motion((first, second))}
        system = MotionSystem()
        moved, pending = system.step(placements, motions, map_, .75)
        self.assertEqual(tuple(moved['unit'].position), (1.75, .5, 2))
        self.assertEqual(pending['unit'].segment_index, 1)
        self.assertEqual(pending['unit'].elapsed, .25)
        self.assertEqual(tuple(placements['unit'].position), (.5, .5, 0))
        self.assertEqual(motions['unit'].elapsed, 0)
        moved, pending = system.step(moved, pending, map_, .75)
        self.assertEqual(tuple(moved['unit'].position), (2.5, .5, 0))
        self.assertEqual(pending, {})
        one_tick, finished = system.step(placements, motions, map_, 20)
        self.assertEqual(one_tick, moved)
        self.assertEqual(finished, {})
        _, empty = system.step(placements, {'unit': Motion(())}, map_, 0)
        self.assertEqual(empty, {})

    def test_variable_projectile_duration_and_split_ticks_agree(self):
        map_ = terrain(3, [0, 0, 0], erosion=0)
        placements = {'arrow': ObjectPlacement('arrow', glm.vec3(.5, .5, 1))}
        for duration in (.25, 2):
            segment = MotionSegment(glm.vec2(.5, .5), glm.vec2(2.5, .5), arc_height(1, 1, 3, duration), duration)
            motions = {'arrow': Motion((segment,))}
            system = MotionSystem()
            midpoint, _ = system.step(placements, motions, map_, duration / 2)
            self.assertEqual(tuple(midpoint['arrow'].position), (1.5, .5, 3))
            current, active = placements, motions
            for _ in range(4):
                current, active = system.step(current, active, map_, duration / 4)
            whole, _ = system.step(placements, motions, map_, duration)
            self.assertEqual(current, whole)
            self.assertEqual(active, {})

    def test_invalid_duration_and_time_are_rejected(self):
        for duration in (0, -1, math.nan, math.inf):
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                MotionSegment(glm.vec2(0), glm.vec2(1), (0, 0, 0), duration)
        with self.assertRaises(ValueError):
            MotionSystem().step({}, {}, terrain(1, [0]), -1)

    def test_map_helpers_continuity_and_simple_movement_choice(self):
        query = TileMotionQuery(.4, 2)
        smooth = terrain(2, [2, 6])
        cliff = terrain(2, [2, 4], erosion=0)
        capped = terrain(2, [2, 6], erosion=1)
        for map_, continuous in ((smooth, True), (cliff, False), (capped, False)):
            for source, end in (((0, 0), (1, 0)), ((1, 0), (0, 0))):
                self.assertEqual(map_.is_continuous_transition(source, end), continuous)
        self.assertEqual(tuple(cliff.world_position((1, 0))), (1.5, .5, 4))
        self.assertEqual(query.segment((0, 0), (1, 0), smooth).height_coefficients[0], 0)
        self.assertLess(query.segment((0, 0), (1, 0), cliff).height_coefficients[0], 0)
        self.assertIsNone(query.segment((0, 0), (1, 0), capped))
        vertical = terrain(1, [2, 4], erosion=0)
        self.assertFalse(vertical.is_continuous_transition((0, 0), (0, 1)))
        self.assertFalse(vertical.is_continuous_transition((0, 1), (0, 0)))
        self.assertIn((1, 0), cliff)
        self.assertIn(glm.vec2(1.99, .5), cliff)
        with self.assertRaises(ValueError):
            cliff.is_continuous_transition((0, 0), (0, 0))
        with self.assertRaises(IndexError):
            cliff.cell_center((2, 0))


class VisibilityTests(unittest.TestCase):
    def test_terrain_objects_disabled_and_excluded_entities(self):
        map_ = terrain(3, [0, 0, 0], erosion=0)
        source, target = glm.vec3(.5, .5, 1), glm.vec3(2.5, .5, 1)
        query = LineOfSightQuery(.05)
        definitions = {'soldier': ObjectArchetype('soldier.svg', height=1.5)}
        placements = {'unit': ObjectPlacement('soldier', glm.vec3(1.5, .5, 0))}
        self.assertTrue(query.is_clear(source, target, {}, {}, map_))
        self.assertFalse(query.is_clear(source, target, placements, definitions, map_))
        self.assertTrue(query.is_clear(source, target, placements, definitions, map_, disabled=('unit',)))
        self.assertTrue(query.is_clear(source, target, placements, definitions, map_, excluded=('unit',)))
        noncollidable = {'soldier': replace(definitions['soldier'], is_collidable=False)}
        self.assertTrue(query.is_clear(source, target, placements, noncollidable, map_))
        hill = terrain(3, [0, 2, 0], erosion=0)
        self.assertFalse(query.is_clear(source, target, {}, {}, hill))
        self.assertTrue(query.is_clear(source + glm.vec3(0, 0, 2), target + glm.vec3(0, 0, 2), {}, {}, hill))

    def test_object_height_is_added_to_tile_height(self):
        map_ = terrain(3, [0, 1, 0], erosion=0)
        query = LineOfSightQuery(.1)
        source, target = glm.vec3(.5, .5, 2), glm.vec3(2.5, .5, 2)
        self.assertFalse(query.is_clear(source, target,
            {'tree': ObjectPlacement('tree', glm.vec3(1.5, .5, 1))},
            {'tree': ObjectArchetype('tree.svg', height=1.5)}, map_))

    def test_short_zero_length_and_out_of_bounds_rays(self):
        map_ = terrain(1, [1])
        query = LineOfSightQuery(.1)
        p = glm.vec3(.5, .5, 2)
        self.assertTrue(query.is_clear(p, p, {}, {}, map_))
        self.assertFalse(query.is_clear(glm.vec3(.5, .5, 0), p, {}, {}, map_))
        self.assertFalse(query.is_clear(p, glm.vec3(1.5, .5, 2), {}, {}, map_))
        for step in (0, -1, math.inf, math.nan):
            with self.assertRaises(ValueError):
                LineOfSightQuery(step)
