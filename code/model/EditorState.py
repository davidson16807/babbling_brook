"""Level-editor values, independent of the game's entity/component stores."""
from dataclasses import dataclass, field

from ..codec.map.PpmImageCodec import PpmImage
from .CameraState import CameraState
from .Map import Map
from .component.instances import ObjectPlacement
from .identifiers import Coordinate, EntityId


@dataclass(frozen=True)
class EditorState:
    image: PpmImage  # Authoritative samples, including heights before erosion.
    map: Map
    placements: dict[EntityId, ObjectPlacement]
    # Always a nonempty list. First is the selection anchor; last is its head.
    cursor: list[Coordinate]
    camera: CameraState = field(default_factory=CameraState)
    viewport: tuple[int, int] = (1280, 720)
    message: str = ""
    running: bool = True
    dirty: bool = False
    quit_requested: bool = False
    cursor_delay: float = 0.0
