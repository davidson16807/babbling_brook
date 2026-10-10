# HUMAN VETTED

from collections import defaultdict

from dataclasses import dataclass, field

from ..model.CameraState import CameraState
from ..model.identifiers import ArchetypeId, EntityId
from ..model.component.zone import Biome, Zone, ZoneDirections, ZoneAdjacency
from ..model.Map import Map
from ..model.store import ArchetypeComponentStores, InstanceComponentStores


@dataclass(frozen=True)
class ExplorerState:
    maps: dict[str, Map] # terrain for each zone that has a map, keyed by zone
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
    biomes: dict[str, Biome] = field(default_factory=dict)
    biome_spawns: set[tuple[str, str]] = field(default_factory=set)
    zones: dict[str, Zone] = field(default_factory=dict)
    zone_directions: dict[str, ZoneDirections] = field(default_factory=dict)
    zone_adjacencies: dict[tuple[str, str], ZoneAdjacency] = field(default_factory=dict)
    colorcodes: dict[str, str] = field(default_factory=dict)
