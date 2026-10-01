# HUMAN VETTED

from dataclasses import dataclass, field

from ..codec.map.PpmImageCodec import PpmImage
from ..model.CameraState import CameraState
from ..model.component.Cycle import Cycle
from ..model.Map import Map
from ..model.identifiers import Coordinate, EntityId
from .EditorContent import EditorContent


@dataclass(frozen=True)
class EditorState:
    content: EditorContent
    map: Map
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
    undo_history: list[EditorContent] = field(default_factory=list)
    redo_history: list[EditorContent] = field(default_factory=list)
    cycles: dict[str, Cycle] = field(default_factory=dict)
    time_warp: float = 0.0
    time_mode: bool = False
    object_step: float | None = None
    selected_objects: frozenset[EntityId] = frozenset()
