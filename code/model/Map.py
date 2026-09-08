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

from .fields import IndexedField, RasterField
from .components.archetypes import TileArchetype
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

    def __contains__(self, position: glm.vec2) -> bool:
        return position in self._corner_heights

    def archetype(self, coordinate: Coordinate) -> TileArchetype:
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
