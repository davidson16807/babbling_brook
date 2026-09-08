from collections import defaultdict


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
                tile = map_.archetype(coordinate)
                coordinates, heights = batches[tile.top_texture, tile.side_texture]
                coordinates.append(coordinate)
                heights.append(map_.corner_heights(coordinate))
        return {textures: tuple(tuple(values) for values in arrays) 
            for textures, arrays in batches.items()}

    def draw(self, model, view):
        # Object collection changes copy Map but share the immutable tile fields.
        key = (model.map._corner_heights, model.map._tiles)
        if self.map != key:
            self.map, self.batches = key, self._build(model.map)
        for (top_texture, side_texture), arrays in self.batches.items():
            self.program.draw(top_texture, side_texture, *arrays, view)

    def release(self):
        self.program.release()
