# HUMAN VETTED

from collections import defaultdict
from math import ceil, floor

from pyglm import glm

from ..program.ViewState import ViewState


class TileView:
    def __init__(self, program):
        self.program = program
        self.map = None
        self.batches = {}

    def _build(self, map_):
        batches = defaultdict(lambda: ([], [], []))

        for y in range(map_.dimensions.y):
            for x in range(map_.dimensions.x):
                coordinate = x, y
                tile = map_.tile(coordinate)
                coordinates, heights, base_heights = batches[tile.top_texture, tile.side_texture]
                surface = map_.corner_heights(coordinate)
                corners = tuple(surface[i][j] for i in range(2) for j in range(2))
                # Keep all flat layers below the lowest corner. The cap then
                # follows the original surface without any inverted side faces.
                cap_base = max(0, min(floor(min(corners)), ceil(max(corners)) - 1))
                for base in range(cap_base):
                    coordinates.append(coordinate)
                    heights.append(glm.mat2(*(base + 1,) * 4))
                    base_heights.append(float(base))
                coordinates.append(coordinate)
                heights.append(surface)
                base_heights.append(float(cap_base))
        return {textures: tuple(tuple(values) for values in arrays) 
            for textures, arrays in batches.items()}

    def draw(self, map_, view_state: ViewState):
        key = (map_._corner_heights, map_._tiles)
        if self.map != key:
            self.map, self.batches = key, self._build(map_)
        for (top_texture, side_texture), arrays in self.batches.items():
            self.program.draw(top_texture, side_texture, *arrays, view_state)

    def release(self):
        self.program.release()
