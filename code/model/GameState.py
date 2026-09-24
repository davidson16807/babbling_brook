# HUMAN VETTED

from collections import defaultdict
from dataclasses import dataclass, field

from .CameraState import CameraState
from .identifiers import ArchetypeId
from .Map import Map
from .store import ArchetypeComponentStores, InstanceComponentStores


@dataclass(frozen=True)
class GameState:
    map: Map
    globals: dict[str, None|bool|int|float|str] # globals for e.g. quest state
    archetypes: ArchetypeComponentStores
    instances: InstanceComponentStores = field(default_factory=InstanceComponentStores)

    inventory: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))
    camera: CameraState = field(default_factory=CameraState)
    # Preserve sub-threshold drags while GameUpdater snaps the displayed azimuth.
    camera_drag_remainder: float = 0.0

    viewport: tuple[int, int] = (1280, 720)
    message: str = "" # contents of a dialog box or message to the player
    running: bool = True
    show_inventory: bool = False
    character_animation_frames: dict[
        tuple[ArchetypeId, str, int, int], tuple[str, float]
    ] = field(default_factory=dict)
