import importlib
import math
import pkgutil
import unittest
from dataclasses import replace

from pyglm import glm

import babbling_brook.codecs
import babbling_brook.model
from babbling_brook.model import GameState
from babbling_brook.model.fields import RasterField, IndexedField
from babbling_brook.model.Map import Map
from babbling_brook.model.components.archetypes import TileArchetype
from babbling_brook.model.components.instances import CharacterAnimationState
from babbling_brook.model.stores import ArchetypeComponentStores


def terrain(width, heights, erosion=float('inf'), tile_ids=None, archetypes=None):
    if archetypes is None:
        archetypes = {'ground': TileArchetype('grass.png', 'ground.png', max_erosion=erosion)}
    dimensions = glm.ivec2(width, len(heights) // width)
    return Map(dimensions, RasterField(dimensions, tuple(heights)),
               IndexedField(archetypes, RasterField(dimensions,
                   tuple(tile_ids or ['ground'] * len(heights)))))


def corners(map_, coordinate):
    h = map_.corner_heights(coordinate)
    return h[0][0], h[1][0], h[1][1], h[0][1]


class TerrainTests(unittest.TestCase):
    def test_adjacent_eroded_tiles_share_both_edge_endpoints(self):
        map_ = terrain(2, [2, 4])
        self.assertEqual(corners(map_, (0, 0)), (2, 2, 2, 2))
        self.assertEqual(corners(map_, (1, 0)), (2, 4, 4, 2))

    def test_corner_includes_diagonal_and_current_tile(self):
        map_ = terrain(2, [2, 5, 7, 9])
        for cell, corner in (((0, 0), 2), ((1, 0), 3), ((0, 1), 1), ((1, 1), 0)):
            self.assertEqual(corners(map_, cell)[corner], 2)

    def test_flat_neighbors_contribute_but_keep_their_own_heights(self):
        archetypes = {
            'flat': TileArchetype('stone.png', 'stone.png'),
            'eroded': TileArchetype('grass.png', 'ground.png', max_erosion=float('inf')),
        }
        for heights in ([2, 4], [6, 4]):
            with self.subTest(heights=heights):
                map_ = terrain(2, heights, tile_ids=['flat', 'eroded'], archetypes=archetypes)
                self.assertEqual(corners(map_, (0, 0)), (heights[0],) * 4)
                edge = corners(map_, (1, 0))
                self.assertEqual((edge[0], edge[3]), (min(heights),) * 2)

    def test_cap_retains_a_cliff(self):
        map_ = terrain(2, [2, 6], erosion=1)
        self.assertEqual(corners(map_, (0, 0)), (2, 2, 2, 2))
        self.assertEqual(corners(map_, (1, 0)), (5, 6, 6, 5))
        self.assertEqual(map_.height(glm.vec2(1, 0.5)), 5)
        self.assertEqual(map_.height(glm.vec2(0.999, 0.5)), 2)

    def test_per_archetype_cap_and_complete_erosion_of_isolated_peak(self):
        heights = [2, 2, 2, 2, 6, 2, 2, 2, 2]
        for cap, expected in ((0, 6), (1.5, 4.5), (float('inf'), 2)):
            with self.subTest(cap=cap):
                archetypes = {'flat': TileArchetype('stone.png', 'stone.png'),
                              'peak': TileArchetype('grass.png', 'ground.png', max_erosion=cap)}
                ids = ['flat'] * 9
                ids[4] = 'peak'
                map_ = terrain(3, heights, tile_ids=ids, archetypes=archetypes)
                self.assertEqual(corners(map_, (1, 1)), (expected,) * 4)
                self.assertEqual(map_.height(glm.vec2(1.5, 1.5)), expected)

    def test_single_tile_has_no_imaginary_lower_neighbors(self):
        map_ = terrain(1, [6])
        self.assertEqual(corners(map_, (0, 0)), (6, 6, 6, 6))

    def test_height_matches_planes_of_exactly_two_triangles(self):
        map_ = terrain(3, [5, 3, 7, 4, 9, 8, 6, 2, 1])
        h00, h10, h11, h01 = corners(map_, (1, 1))
        a, b, c, d = (glm.vec3(1, 1, h00), glm.vec3(2, 1, h10),
                      glm.vec3(2, 2, h11), glm.vec3(1, 2, h01))
        triangles = ((a, b, c), (a, c, d))
        self.assertEqual(len(triangles), 2)
        self.assertEqual(len({tuple(vertex) for triangle in triangles for vertex in triangle}), 4)
        for a, b, c in triangles:
            normal = glm.cross(b - a, c - a)
            self.assertGreater(normal.z, 0)
            for weights in ((0.2, 0.3, 0.5), (0.6, 0.2, 0.2), (0.1, 0.8, 0.1)):
                point = weights[0] * a + weights[1] * b + weights[2] * c
                sampled = glm.vec3(point.x, point.y, map_.height(glm.vec2(point)))
                self.assertAlmostEqual(glm.dot(normal, sampled - a), 0, places=5)
        # The diagonal is continuous and follows the chosen 00--11 edge.
        self.assertAlmostEqual(map_.height(glm.vec2(1.5, 1.5)), 2)

    def test_triangle_height_is_not_bilinear_or_a_center_fan(self):
        map_ = terrain(3, [2, 6, 6, 6, 6, 6, 6, 6, 6])
        self.assertEqual(corners(map_, (1, 1)), (2, 6, 6, 6))
        self.assertEqual(map_.height(glm.vec2(1.75, 1.25)), 5)
        self.assertEqual(map_.height(glm.vec2(1.25, 1.75)), 5)
        self.assertEqual(map_.height(glm.vec2(1.5, 1.5)), 4)

    def test_bounds_and_row_major_indexing(self):
        map_ = terrain(3, [1, 2, 3, 4, 5, 6], erosion=0)
        self.assertEqual(map_.height(glm.vec2(2.5, 1.5)), 6)
        for xy in ((-0.001, 0), (0, -0.001), (3, 0), (0, 2), (math.nan, 0), (0, math.inf)):
            with self.subTest(xy=xy):
                position = glm.vec2(*xy)
                self.assertNotIn(position, map_)
                self.assertIsNone(map_.height(position))
                with self.assertRaises(IndexError):
                    map_.tile(tuple(position))
        with self.assertRaises(IndexError):
            corners(map_, (3, 0))

    def test_invalid_map_data_and_erosion_are_rejected(self):
        for value in (-1, -math.inf, math.nan):
            with self.subTest(value=value), self.assertRaises(ValueError):
                TileArchetype('grass.png', 'ground.png', max_erosion=value)
        archetypes = {'ground': TileArchetype('grass.png', 'ground.png')}
        for dimensions, heights, ids in (
            ((0, 1), (), ()), ((2, 2), (1,), ('ground',)),
            ((1, 1), (math.nan,), ('ground',)), ((1, 1), (1,), ('missing',)),
        ):
            with self.subTest(dimensions=dimensions, heights=heights), self.assertRaises(ValueError):
                Map(glm.ivec2(*dimensions), RasterField(glm.ivec2(*dimensions), heights),
                    IndexedField(archetypes, RasterField(glm.ivec2(*dimensions), ids)))


class ModelTests(unittest.TestCase):
    def test_all_model_and_codec_modules_import_without_graphics_dependencies(self):
        for package in (babbling_brook.model, babbling_brook.codecs):
            for module in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
                importlib.import_module(module.name)

    def test_mutable_defaults_are_not_shared_and_vectors_can_be_replaced(self):
        map_ = terrain(1, [1])
        archetypes = ArchetypeComponentStores()
        first, second = GameState(map_, {}, archetypes), GameState(map_, {}, archetypes)
        first.inventory['apple'] += 2
        first.instances.positionables['player'] = glm.vec3(0.5, 0.5, 1)
        self.assertEqual(second.inventory['apple'], 0)
        self.assertEqual(second.instances.positionables, {})
        old = CharacterAnimationState()
        new = replace(old, facing=glm.vec2(1, 0))
        self.assertEqual(tuple(old.facing), (0, 1))
        self.assertEqual(tuple(new.facing), (1, 0))
