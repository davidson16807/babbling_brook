from collections import defaultdict
from ..programs.ViewState import ViewState


class TileView:
    def __init__(self, program):
        self.program = program
        self.map = None
        self.batches = {}

    def _build(self, map_):
        batches = defaultdict(lambda: ([], []))

        for y in range(map_.dimensions.y):
            for x in range(map_.dimensions.x):
                coordinate = x, y
                tile = map_.tile(coordinate)
                coordinates, heights = batches[tile.top_texture, tile.side_texture]
                coordinates.append(coordinate)
                heights.append(map_.corner_heights(coordinate))
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
