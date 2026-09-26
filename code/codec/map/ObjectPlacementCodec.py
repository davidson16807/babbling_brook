# HUMAN VETTED

from pyglm import glm

from ...model.Map import Map
from .PpmImageCodec import PpmImage
from ...model.component.instances import ObjectPlacement
from ...model.identifiers import ArchetypeId, EntityId


class ObjectPlacementCodec:
    def __init__(self, object_palette: dict[int, ArchetypeId], map: Map,
                 disable_validation: bool = False):
        self.object_palette = object_palette
        self.map = map
        self.disable_validation = disable_validation

    def decode(self, image: PpmImage) -> dict[EntityId, ObjectPlacement]:
        if not self.disable_validation and (image.width, image.height) != tuple(self.map.dimensions):
            raise ValueError("Object image and tile map dimensions must agree")
        placements = {}
        for i, (_, _, blue) in enumerate(image.pixels):
            if blue == 0:
                continue
            try:
                archetype = self.object_palette[blue]
            except KeyError as error:
                if self.disable_validation:
                    continue
                raise ValueError(f"Unknown object palette index: {blue}") from error
            coordinate = i % image.width, i // image.width
            position = glm.vec2(*coordinate) + glm.vec2(0.5)
            placements[str(coordinate)] = ObjectPlacement(
                archetype, glm.vec3(position, self.map.height(position))
            )
        return placements
