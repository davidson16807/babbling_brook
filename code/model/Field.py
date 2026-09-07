# HUMAN WRITTEN

from typing import TypeVar, Generic
from pyglm import glm

from .identifiers import Coordinate

T = TypeVar('T')

'''
`Field` represents a 2d field in the mathematical sense, ℝ²→T,
where each point in 2d space is mapped to a value of type T.
This is done by discretizing the field into cells within a raster.

If ever we introduce procedural fields, this will be renamed `RasterField`.
'''

class Field(Generic[T]):
    def __init__(self, dimensions: glm.ivec2, contents: tuple[T, ...]):
        self.dimensions = glm.ivec2(dimensions)
        if self.dimensions.x <= 0 or self.dimensions.y <= 0:
            raise ValueError("Map dimensions must be positive")
        self.contents = tuple(contents)
        if len(self.contents) != self.dimensions.x * self.dimensions.y:
            raise ValueError("Field contents must match dimensions")

    def _coordinate(self, position: glm.vec2) -> Coordinate:
        cell = glm.floor(position)
        return int(cell.x), int(cell.y)

    def _index(self, coordinate: Coordinate) -> int:
        if coordinate not in self:
            raise IndexError(f"Tile coordinate outside map: {coordinate}")
        x, y = coordinate
        return y * self.dimensions.x + x

    def __contains__(self, position: glm.vec2) -> bool:
        x, y = position
        return 0 <= x < self.dimensions.x and 0 <= y < self.dimensions.y

    def __getitem__(self, coordinate: Coordinate) -> T:
        return self.contents[self._index(coordinate)]

    def __call__(self, position: glm.vec2) -> T:
        return self[self._coordinate(position)]
