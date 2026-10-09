"""Editable level data captured together by undo/redo history."""

from dataclasses import dataclass, field

from pyglm import glm

from ..codec.map.PpmImageCodec import PpmImage
from ..model.component.instance import ObjectPlacement
from ..model.identifiers import EntityId


@dataclass(frozen=True)
class EditorContent:
    # Authoritative samples, including heights before erosion.
    image: PpmImage
    # Treat dictionaries and their GLM vectors as values: replace, don't mutate.
    # Billboards and boxes alike; the archetype decides which.
    placements: dict[EntityId, ObjectPlacement] = field(default_factory=dict)
    # Named character placements retain their ECS entity IDs and are always
    # serialized in the game's placements table.
    character_instances: dict[EntityId, ObjectPlacement] = field(default_factory=dict)

    zone: str = ""

    def object_center(self, entities):
        positions = [item.position for table in (self.placements, self.character_instances)
                     for key, item in table.items() if key in entities]
        return sum(positions, glm.vec3(0)) / len(positions) if positions else None
