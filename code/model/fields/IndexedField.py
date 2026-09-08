
from collections.abc import Mapping
from typing import Generic, TypeVar

from pyglm import glm

from ..identifiers import Coordinate
from .RasterField import RasterField


K = TypeVar('K')
T = TypeVar('T')


class IndexedField(Generic[K, T]):
    def __init__(self, indexed: Mapping[K, T], index: RasterField[K]):
        self.indexed = indexed
        self.index = index
        self.dimensions = index.dimensions

    def __contains__(self, position: glm.vec2) -> bool:
        return position in self.index and self.index(position) in self.indexed

    def __getitem__(self, coordinate: Coordinate) -> T:
        return self.indexed[self.index[coordinate]]

    def __call__(self, position: glm.vec2) -> T:
        return self.indexed[self.index(position)]
