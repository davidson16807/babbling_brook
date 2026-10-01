"""Editable level data captured together by undo/redo history."""

from dataclasses import dataclass, field

from ..codec.map.PpmImageCodec import PpmImage
from ..model.component.instances import BillboardPlacement, BoxPlacement
from ..model.identifiers import EntityId


@dataclass(frozen=True)
class EditorContent:
    # Authoritative samples, including heights before erosion.
    image: PpmImage
    # Treat dictionaries and their GLM vectors as values: replace, don't mutate.
    billboards: dict[EntityId, BillboardPlacement] = field(default_factory=dict)
    boxes: dict[EntityId, BoxPlacement] = field(default_factory=dict)
    # Named character placements retain their ECS entity IDs and are always
    # serialized in the game's billboards table.
    character_instances: dict[EntityId, BillboardPlacement] = field(default_factory=dict)
