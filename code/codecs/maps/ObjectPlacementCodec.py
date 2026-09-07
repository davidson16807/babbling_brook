from pyglm import glm

from ...model.Map import Map
from ...model.PpmImage import PpmImage
from ...model.components.instances import ObjectPlacement
from ...model.identifiers import ArchetypeId


class ObjectPlacementCodec:
    def __init__(self, object_palette: dict[int, ArchetypeId], map: Map):
        self.object_palette = object_palette
        self.map = map

    def decode(self, image: PpmImage) -> list[ObjectPlacement]:
        if (image.width, image.height) != tuple(self.map.dimensions):
            raise ValueError("Object image and tile map dimensions must agree")
        placements = []
        for i, (_, _, blue) in enumerate(image.pixels):
            if blue == 0:
                continue
            try:
                archetype = self.object_palette[blue]
            except KeyError as error:
                raise ValueError(f"Unknown object palette index: {blue}") from error
            coordinate = i % image.width, i // image.width
            position = glm.vec2(*coordinate) + glm.vec2(0.5)
            placements.append(ObjectPlacement(
                str(coordinate), archetype, glm.vec3(position, self.map.height(position))
            ))
        return placements
