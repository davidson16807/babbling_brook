"""Level-editor data, independent of the game's entities and rules."""
from dataclasses import dataclass, field
from pathlib import Path

from ..codec.map.PpmImageCodec import PpmImage
from .CameraState import CameraState
from .Map import Map
from .component.archetypes import ObjectArchetype, TileArchetype
from .component.instances import ObjectPlacement
from .identifiers import ArchetypeId, Coordinate, EntityId


@dataclass(frozen=True)
class EditorState:
    filename: Path
    image: PpmImage
    saved_image: PpmImage
    map: Map
    placements: dict[EntityId, ObjectPlacement]
    tile_palette: dict[int, ArchetypeId]
    object_palette: dict[int, ArchetypeId]
    tile_archetypes: dict[ArchetypeId, TileArchetype]
    object_archetypes: dict[ArchetypeId, ObjectArchetype]
    cursor: Coordinate
    camera: CameraState = field(default_factory=CameraState)
    viewport: tuple[int, int] = (1280, 720)
    message: str = ''
    running: bool = True
    quit_pending: bool = False
    cursor_delay: float = 0.0
    undo: tuple[PpmImage, ...] = ()
    redo: tuple[PpmImage, ...] = ()

    @property
    def dirty(self) -> bool:
        return self.image != self.saved_image
