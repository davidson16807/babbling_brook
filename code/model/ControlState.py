from dataclasses import dataclass

from ..messages import MouseButton


@dataclass(frozen=True)
class ControlState:
    pressed_keys: frozenset[str] = frozenset()
    pressed_mouse_buttons: frozenset[MouseButton] = frozenset()
