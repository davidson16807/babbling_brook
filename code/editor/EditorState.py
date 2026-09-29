# HUMAN VETTED

from dataclasses import dataclass, field

from ..codec.map.PpmImageCodec import PpmImage
from ..model.CameraState import CameraState
from ..model.component.Cycle import Cycle
from ..model.Map import Map
from ..model.component.instances import ObjectPlacement
from ..model.identifiers import Coordinate, EntityId


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
    channel: int | None = None  # PPM R/G/B index; None selects zoom.
    clipboard: PpmImage | None = None
    undo_history: list[PpmImage] = field(default_factory=list)
    redo_history: list[PpmImage] = field(default_factory=list)
    cycles: dict[str, Cycle] = field(default_factory=dict)
    time_warp: float = 1.0
