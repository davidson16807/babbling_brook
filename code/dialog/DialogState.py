"""All dialog interaction state; dictionaries and tuples are replaced, not mutated."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DialogState:
    viewport: tuple[int, int] = (1180, 760)
    phrases: tuple[dict, ...] = ()
    selected: int | None = None
    selected_part: int | None = None
    next_id: int = 1
    choices: tuple[tuple[str, tuple[str, ...]], ...] = ()
    inventory_scroll: int = 0
    form_scroll: int = 0
    sentence_scroll: int = 0
    pointer: tuple[float, float] = (0, 0)
    pressed: tuple | None = None
    press_position: tuple[float, float] = (0, 0)
    dragging: bool = False
    transcript: tuple[tuple[str, bool], ...] = ()
    command: dict | None = None
    message: str = 'Drag a word into the sentence. Click a word to choose its form.'
    running: bool = True
