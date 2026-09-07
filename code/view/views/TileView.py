from collections import defaultdict


class TileView:
    def __init__(self, program):
        self.program = program
        self.map = None
        self.batches = {}

    def _build(self, map_):
        batches = defaultdict(lambda: ([], [], [], [], [], []))

        def heights(coordinate):
            x, y = coordinate
            min_height = map_.min_height(coordinate)
            return tuple(
                map_.corner_height((xi, yi), min_height)
                for yi in (y, y + 1)
                for xi in (x, x + 1)
            )

        for y in range(map_.dimensions.y):
            for x in range(map_.dimensions.x):
                coordinate = x, y
                tile = map_.archetype(coordinate)
                (coordinates, southwest, southeast, northwest, northeast,
                 exposed_sides) = batches[tile.texture]
                coordinates.append(coordinate)
                sw, se, nw, ne = heights(coordinate)
                southwest.append(sw)
                southeast.append(se)
                northwest.append(nw)
                northeast.append(ne)
                exposed_sides.append(tile.show_exposed_sides)
        return {texture: tuple(tuple(values) for values in arrays) for texture, arrays in batches.items()}

    def draw(self, model, view):
        # Object collection changes copy Map but share the immutable tile fields.
        key = (model.map._max_heights, model.map._tile_archetype_ids)
        if self.map != key:
            self.map, self.batches = key, self._build(model.map)
        for texture, arrays in self.batches.items():
            self.program.draw(texture, *arrays, view)

    def release(self):
        self.program.release()
