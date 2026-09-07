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

    def __contains__(self, position: glm.vec2) -> bool:
        return position in self._max_heights

    def archetype(self, coordinate: Coordinate) -> TileArchetype:
        return self._tile_archetypes[self._tile_archetype_ids[coordinate]]

    def corner_height(self, coordinate: Coordinate, min_height: float) -> float:
        x,y = coordinate
        return max(
                min(
                    self._max_heights[(xj, yj)]
                    for xj in (x-1, x)
                    for yj in (y-1, y)
                    if (xj, yj) in self._max_heights
                ), 
                min_height
            )

    def height(self, position: glm.vec2) -> float | None:
        if position not in self.max_heights:
            return None

        height = self._max_heights[coordinate]
        archetype = self._tile_archetypes[self._type_archetype_ids[coordinate]]
        if archetype.max_erosion <= 0:
            return height, height, height, height

        min_height = height - archetype.max_erosion
        coordinate = self._coordinate(position)
        h00, h01, h10, h11 = (
            self.corner_height(coordinate, min_height)
            for y in (y,y+1)
            for x in (x,x+1)
        )

        local = position - glm.vec2(*coordinate)
        if local.y <= local.x:
            weights = glm.vec3(1 - local.x, local.x - local.y, local.y)
            heights = glm.vec3(h00, h10, h11)
        else:
            weights = glm.vec3(1 - local.y, local.x, local.y - local.x)
            heights = glm.vec3(h00, h11, h01)
        return glm.dot(weights, heights)
