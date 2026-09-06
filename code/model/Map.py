from __future__ import annotations

from pyglm import glm
from .model import ArchetypeComponents, Map

Coordinate: TypeAlias = tuple[int, int]

class Map:

    def __init__(self, dimensions: glm.ivec2,
        tile_heights: tuple[float, ...],
        tile_archetypes: ArchetypeComponents,
    ):
        self.dimensions = dimensions
        self._tile_heights = _tile_heights
        self._tile_archetypes = _tile_archetypes

    def _compatible_sample(
        self, sample: Coordinate, current: Coordinate
    ) -> float:
        clamped = (
            min(max(sample[0], 0), self.map.width - 1),
            min(max(sample[1], 0), self.map.height - 1),
        )
        current_height = self.map.height_at_tile(current)
        sample_tile_id = self.map.tile_archetype_at(clamped)
        if not self.archetypes.tiles[sample_tile_id].smooth_vertices:
            return current_height
        return self.map.height_at_tile(clamped)

    def _coordinate(self, position: glm.vec2) -> Coordinate:
        return (int(glm.floor(position.x)), int(glm.floor(position.y)))

    def _index(self, coordinate: Coordinate) -> int:
        return coordinate.y * self.max_x + coordinate.x

    def __contains__(self, position: glm.vec2) -> bool:
        x,y = self._coordinate(position)
        return 0 <= x < self.max_x and 0 <= y < self.max_y

    def archetype(position: glm.vec2) -> ArchetypeId:
        if coordinate not in self:
            raise IndexError(f"tile coordinate outside map: {coordinate}")
        coordinate = self._coordinate(position)
        tile_id = self._tile_archetypes[self._index(coordinate)]
        return self._tile_archetypes.tiles[tile_id]

    def height(self, position: glm.vec2) -> float:
        coordinate = self._coordinate(position)
        if coordinate not in self:
            return None
        index = self.index(coordinate)
        tile = self._tile_archetypes[index]
        if not tile.smooth_vertices:
            return self._tile_heights[index]
        else:
            ...
