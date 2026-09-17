# HUMAN VETTED

"""
`Map` stores all properties of tiles on a map.

Cells occupy [x, x + 1) by [y, y + 1).
Heights are specified by `max_heights`, which represents the tallest height each tile may achieve.
Tiles are characterized by this height and an archetype,
which represents material like stone work or grass.
Certain materials like stone work are never subject to erosion,
therefore they are flat on top and `max_height` is their height throughout.
Other materials like grass are subject to erosion,
and in this case the actual height for each corner of the vertex is
set to the minimum of their neighbors down to that archetype's `max_erosion`.
As a simplifying assumption, we assume all eroded material washes away
leaving no deposits upon adjacent down-hill neighboring tiles.
"""

from math import isfinite

from pyglm import glm

from .field import IndexedField, RasterField
from .component.archetypes import TileArchetype
from .identifiers import ArchetypeId, Coordinate


def TileCornerHeightsField(
    max_heights: RasterField[float],
    tiles: IndexedField[ArchetypeId, TileArchetype],
) -> RasterField[glm.mat2]:
    dimensions = max_heights.dimensions

    if tuple(tiles.dimensions) != tuple(dimensions):
        raise ValueError("Map fields must have matching dimensions")

    def corner_height(coordinate: Coordinate, min_height: float) -> float:
        x, y = coordinate
        return max(
            min(
                max_heights[(xj, yj)]
                for xj in (x - 1, x)
                for yj in (y - 1, y)
                if (xj, yj) in max_heights
            ),
            min_height,
        )

    def corner_heights(coordinate: Coordinate) -> glm.mat2:
        x, y = coordinate
        min_height = max_heights[coordinate] - tiles[coordinate].max_erosion
        southwest, southeast, northwest, northeast = tuple(
            corner_height((xj, yj), min_height)
            for yj in (y, y + 1)
            for xj in (x, x + 1)
        )
        return glm.mat2(southwest, northwest, southeast, northeast)

    return RasterField(
        dimensions,
        tuple(
            corner_heights((x, y))
            for y in range(dimensions.y)
            for x in range(dimensions.x)
        ),
    )

class Map:
    def __init__(
        self,
        dimensions: glm.ivec2,
        max_heights: RasterField[float],
        tiles: IndexedField[ArchetypeId, TileArchetype],
    ):
        self.dimensions = glm.ivec2(dimensions)
        if tuple(max_heights.dimensions) != tuple(self.dimensions) or tuple(tiles.dimensions) != tuple(self.dimensions):
            raise ValueError("Map fields must have matching dimensions")
        if any(not isfinite(height) for height in max_heights.contents):
            raise ValueError("Map heights must be finite")
        try:
            self._corner_heights = TileCornerHeightsField(max_heights, tiles)
        except KeyError as error:
            raise ValueError(f"Unknown tile archetype: {error.args[0]!r}") from error
        self._tiles = tiles

    def _coordinate(self, position: glm.vec2) -> Coordinate:
        cell = glm.floor(position)
        return int(cell.x), int(cell.y)

    def __contains__(self, position: Coordinate | glm.vec2) -> bool:
        """Bounds membership for integer cells and continuous XY positions."""
        return position in self._corner_heights

    def tile(self, coordinate: Coordinate) -> TileArchetype:
        return self._tiles[coordinate]

    def corner_heights(self, coordinate: Coordinate) -> glm.mat2:
        return self._corner_heights[coordinate]

    def height(self, position: glm.vec2) -> float | None:
        if position not in self:
            return None
        coordinate = self._coordinate(position)
        h = self._corner_heights[coordinate]
        local = position - glm.vec2(*coordinate)
        if local.y <= local.x:
            weights = glm.vec3(1 - local.x, local.x - local.y, local.y)
            heights = glm.vec3(h[0][0], h[1][0], h[1][1])
        else:
            weights = glm.vec3(1 - local.y, local.x, local.y - local.x)
            heights = glm.vec3(h[0][0], h[1][1], h[0][1])
        return glm.dot(weights, heights)

    def cell_center(self, coordinate: Coordinate) -> glm.vec2:
        """Horizontal center of an integer tile coordinate inside this map."""
        x, y = coordinate
        if x != int(x) or y != int(y):
            raise ValueError("Expected an integer tile coordinate")
        if coordinate not in self:
            raise IndexError(f"Tile coordinate outside map: {coordinate}")
        return glm.vec2(x + 0.5, y + 0.5)

    def world_position(self, coordinate: Coordinate) -> glm.vec3:
        center = self.cell_center(coordinate)
        return glm.vec3(center, self.height(center))

    def is_continuous_transition(
        self, source: Coordinate, destination: Coordinate, tolerance: float = 1e-5,
    ) -> bool:
        """Compare shared-edge midpoint heights from two orthogonal neighbors.

        Uses each tile's own geometry, so capped erosion can still leave a cliff.
        This describes the center-to-center crossing, not every point on the edge.
        """
        if not isfinite(tolerance) or tolerance < 0:
            raise ValueError("tolerance must be finite and nonnegative")
        self.cell_center(source)
        self.cell_center(destination)
        dx, dy = destination[0] - source[0], destination[1] - source[1]
        if abs(dx) + abs(dy) != 1:
            raise ValueError("Tiles must be orthogonally adjacent")
        a, b = self.corner_heights(source), self.corner_heights(destination)
        if dx:
            i, j = (1, 0) if dx > 0 else (0, 1)
            before, after = (a[i][0] + a[i][1]) / 2, (b[j][0] + b[j][1]) / 2
        else:
            i, j = (1, 0) if dy > 0 else (0, 1)
            before, after = (a[0][i] + a[1][i]) / 2, (b[0][j] + b[1][j]) / 2
        return abs(before - after) <= tolerance
