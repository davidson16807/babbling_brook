from collections import defaultdict

from pyglm import glm


class TileView:
    def __init__(self, program):
        self.program = program
        self.map = None
        self.batches = {}

    def _build(self, map_):
        batches = defaultdict(lambda: ([], []))

        def height_matrix(coordinate):
            x, y = coordinate
            min_height = map_.min_height(coordinate)
            southwest, southeast, northwest, northeast = tuple(
                map_.corner_height((xi, yi), min_height)
                for yi in (y, y + 1)
                for xi in (x, x + 1)
            )
            return glm.mat2(southwest, northwest, southeast, northeast)

        for y in range(map_.dimensions.y):
            for x in range(map_.dimensions.x):
                coordinate = x, y
                tile = map_.archetype(coordinate)
                coordinates, heights = batches[tile.top_texture, tile.side_texture]
                coordinates.append(coordinate)
                heights.append(height_matrix(coordinate))
        return {textures: tuple(tuple(values) for values in arrays) for textures, arrays in batches.items()}

    def draw(self, model, view):
        # Object collection changes copy Map but share the immutable tile fields.
        key = (model.map._max_heights, model.map._tile_archetype_ids)
        if self.map != key:
            self.map, self.batches = key, self._build(model.map)
        for (top_texture, side_texture), arrays in self.batches.items():
            self.program.draw(top_texture, side_texture, *arrays, view)

    def release(self):
        self.program.release()
