# HUMAN VETTED

from collections.abc import Mapping
from typing import Generic, TypeVar

from pyglm import glm

from ..identifiers import Coordinate
from .RasterField import RasterField


K = TypeVar('K')
T = TypeVar('T')


class IndexedField(Generic[K, T]):
    def __init__(self, indexed: Mapping[K, T], index: RasterField[K], fallback: T):
        self.indexed = indexed
        self.index = index
        self.dimensions = index.dimensions
        self.fallback = fallback

    def __contains__(self, position: glm.vec2) -> bool:
        return position in self.index and self.index(position) in self.indexed

    def __getitem__(self, coordinate: Coordinate) -> T:
        if coordinate not in self.index: return self.fallback
        index = self.index[coordinate]
        if index not in self.indexed: return self.fallback
        return self.indexed[index]

    def __call__(self, position: glm.vec2) -> T:
        if position not in self.index: return self.fallback
        index = self.index(position)
        if index not in self.indexed: return self.fallback
        return self.indexed[index]
