from math import isfinite

from pyglm import glm

from ...model.Map import Map
from .PpmImageCodec import PpmImage
from ...model.fields import IndexedField, RasterField
from ...model.components.archetypes import TileArchetype
from ...model.identifiers import ArchetypeId


class MapCodec:
    def __init__(self, tile_palette: dict[int, ArchetypeId],
                 tile_archetypes: dict[ArchetypeId, TileArchetype],
                 height_scale: float = 0.5):
        if not isfinite(height_scale) or height_scale <= 0:
            raise ValueError("height_scale must be finite and positive")
        self.tile_palette = tile_palette
        self.tile_archetypes = tile_archetypes
        self.height_scale = height_scale

    def decode(self, image: PpmImage) -> Map:
        try:
            tile_ids = tuple(self.tile_palette[g] for _, g, _ in image.pixels)
        except KeyError as error:
            raise ValueError(f"Unknown tile palette index: {error.args[0]}") from error
        dimensions = glm.ivec2(image.width, image.height)
        max_heights = RasterField(
            dimensions,
            tuple(red * self.height_scale for red, _, _ in image.pixels),
        )
        tile_archetype_ids = RasterField(dimensions, tile_ids)
        tiles = IndexedField(self.tile_archetypes, tile_archetype_ids)
        return Map(dimensions, max_heights, tiles)
