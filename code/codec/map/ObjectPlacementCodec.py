"""Decode the shared blue-channel palette into ECS placement components.

Billboard and box archetypes share the palette and decode to the same
`ObjectPlacement` table; archetype tables are used only for validation.
"""

from pyglm import glm

from ...model.Map import Map
from .PpmImageCodec import PpmImage
from ...model.component.instance import ObjectPlacement
from ...model.identifiers import ArchetypeId, EntityId


class ObjectPlacementCodec:
    def __init__(self, object_palette: dict[int, ArchetypeId], map: Map,
                 disable_validation: bool = False, box_archetypes=None, billboard_archetypes=None, zone=""):
        self.zone = zone
        self.object_palette = object_palette
        box_archetypes = box_archetypes or {}
        if billboard_archetypes is not None:
            for key in object_palette.values():
                if key in box_archetypes and key in billboard_archetypes:
                    raise ValueError(f"Ambiguous object palette entry: {key}")
                if key not in box_archetypes and key not in billboard_archetypes:
                    raise ValueError(f"Unknown object palette entry: {key}")
        self.map = map
        self.disable_validation = disable_validation

    def decode(self, image: PpmImage) -> dict[EntityId, ObjectPlacement]:
        if not self.disable_validation and (image.width, image.height) != tuple(self.map.dimensions):
            raise ValueError("Object image and tile map dimensions must agree")
        objects = {}
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
            origin = glm.vec3(position, self.map.height(position))
            objects[str(coordinate)] = ObjectPlacement(archetype, self.zone, origin)
        return objects
