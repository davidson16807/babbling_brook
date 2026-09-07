from collections import defaultdict


class TileView:
    def __init__(self, program):
        self.program = program
        self.map = None
        self.batches = {}

    def _build(self, map_):
        batches = defaultdict(lambda: ([], [], [], [], [], [], [], [], [], []))

        def heights(coordinate):
            x, y = coordinate
            min_height = map_.min_height(coordinate)
            return tuple(
                map_.corner_height((xi, yi), min_height)
                for yi in (y, y + 1)
                for xi in (x, x + 1)
            )

        def lower_heights(neighbor, first, second):
            if neighbor not in map_:
                return 0.0, 0.0
            min_height = map_.min_height(neighbor)
            return (map_.corner_height(first, min_height),
                    map_.corner_height(second, min_height))

        for y in range(map_.dimensions.y):
            for x in range(map_.dimensions.x):
                coordinate = x, y
                tile = map_.archetype(coordinate)
                (coordinates, southwest, southeast, northwest, northeast,
                 west_lower, east_lower, south_lower, north_lower, exposed_sides) = batches[tile.texture]
                coordinates.append(coordinate)
                sw, se, nw, ne = heights(coordinate)
                southwest.append(sw)
                southeast.append(se)
                northwest.append(nw)
                northeast.append(ne)
                if tile.show_exposed_sides:
                    west_lower.append(lower_heights((x-1, y), (x, y), (x, y+1)))
                    east_lower.append(lower_heights((x+1, y), (x+1, y), (x+1, y+1)))
                    south_lower.append(lower_heights((x, y-1), (x, y), (x+1, y)))
                    north_lower.append(lower_heights((x, y+1), (x, y+1), (x+1, y+1)))
                else:
                    west_lower.append((0.0, 0.0))
                    east_lower.append((0.0, 0.0))
                    south_lower.append((0.0, 0.0))
                    north_lower.append((0.0, 0.0))
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
