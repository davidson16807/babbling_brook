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

from .Field import Field
from .components.archetypes import TileArchetype
from .components.instances import ObjectPlacement
from .identifiers import ArchetypeId, Coordinate


class Map:
    def __init__(
        self,
        dimensions: glm.ivec2,
        max_heights: Field[float],
        tile_archetype_ids: Field[ArchetypeId],
        tile_archetypes: dict[ArchetypeId, TileArchetype],
    ):
        self.dimensions = glm.ivec2(dimensions)
        if tuple(max_heights.dimensions) != tuple(dimensions) or tuple(tile_archetype_ids.dimensions) != tuple(dimensions):
            raise ValueError("Map fields must have matching dimensions")
        self.static_objects: dict = {}
        self._max_heights = max_heights
        self._tile_archetype_ids = tile_archetype_ids
        self._tile_archetypes = tile_archetypes

    def _coordinate(self, position: glm.vec2) -> Coordinate:
        cell = glm.floor(position)
        return int(cell.x), int(cell.y)

    def __contains__(self, position: glm.vec2) -> bool:
        return position in self._max_heights

    def archetype(self, coordinate: Coordinate) -> TileArchetype:
        return self._tile_archetypes[self._tile_archetype_ids[coordinate]]

    def min_height(self, coordinate: Coordinate) -> float:
        return self._max_heights[coordinate] - self.archetype(coordinate).max_erosion

    def corner_height(self, coordinate: Coordinate, min_height: float) -> float:
        x,y = coordinate
        return (
            max(
                min(
                    self._max_heights[(xj, yj)]
                    for xj in (x-1, x)
                    for yj in (y-1, y)
                    if (xj, yj) in self._max_heights
                ), 
                min_height
            )
        )

    def height(self, position: glm.vec2) -> float | None:
        if position not in self:
            return None
        coordinate = self._coordinate(position)

        x, y = coordinate
        min_height = self.min_height(coordinate)
        h00, h10, h01, h11 = tuple(
            self.corner_height((xj, yj), min_height)
            for yj in (y, y + 1) 
            for xj in (x, x + 1)
        )

        local = position - glm.vec2(*coordinate)
        if local.y <= local.x:
            weights = glm.vec3(1 - local.x, local.x - local.y, local.y)
            heights = glm.vec3(h00, h10, h11)
        else:
            weights = glm.vec3(1 - local.y, local.x, local.y - local.x)
            heights = glm.vec3(h00, h11, h01)
        return glm.dot(weights, heights)
