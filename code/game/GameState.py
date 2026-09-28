# HUMAN VETTED

from collections import defaultdict
from dataclasses import dataclass, field

from ..model.CameraState import CameraState
from ..model.identifiers import ArchetypeId, EntityId
from ..model.component.Map import Map as MapDefinition
from ..model.Map import Map
from ..model.store import ArchetypeComponentStores, InstanceComponentStores


@dataclass(frozen=True)
class GameState:
    map: Map
    globals: dict[str, None|bool|int|float|str] # globals for e.g. quest state
    archetypes: ArchetypeComponentStores
    instances: InstanceComponentStores = field(default_factory=InstanceComponentStores)

    inventory: defaultdict[tuple[EntityId, str], int] = field(default_factory=lambda: defaultdict(int))
    camera: CameraState = field(default_factory=CameraState)

    viewport: tuple[int, int] = (1280, 720)
    message: str = "" # contents of a dialog box or message to the player
    running: bool = True
    show_inventory: bool = False
    character_animation_frames: dict[
        tuple[ArchetypeId, str, int, int], tuple[str, float]
    ] = field(default_factory=dict)
    maps: dict[int, MapDefinition] = field(default_factory=dict)
