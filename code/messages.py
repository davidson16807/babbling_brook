from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntFlag, auto
from typing import TypeAlias

from pyglm import glm

class MouseButton(Enum):
    LEFT = auto()
    MIDDLE = auto()
    RIGHT = auto()


class ButtonAction(Enum):
    RELEASE = auto()
    PRESS = auto()


class KeyboardAction(Enum):
    RELEASE = auto()
    PRESS = auto()
    REPEAT = auto()


class KeyboardModifiers(IntFlag):
    NONE = 0
    SHIFT = auto()
    CTRL = auto()
    ALT = auto()
    SUPER = auto()
    CAPS = auto()
    NUM = auto()


@dataclass(frozen=True, slots=True)
class KeyboardMessage:
    key: str
    action: KeyboardAction
    modifiers: KeyboardModifiers = KeyboardModifiers.NONE


@dataclass(frozen=True, slots=True)
class MouseMotionMessage:
    position: glm.vec2
    offset: glm.vec2


@dataclass(frozen=True, slots=True)
class MouseButtonMessage:
    button: MouseButton
    action: ButtonAction
    modifiers: KeyboardModifiers = KeyboardModifiers.NONE


@dataclass(frozen=True, slots=True)
class ScrollMessage:
    offset: glm.vec2


@dataclass(frozen=True, slots=True)
class WindowResizeMessage:
    size: tuple[int, int]


@dataclass(frozen=True)
class FocusLostMessage:
    pass


@dataclass(frozen=True, slots=True)
class QuitMessage:
    pass


@dataclass(frozen=True, slots=True)
class TickMessage:
    seconds: float


Message: TypeAlias = (
    MouseMotionMessage
    | MouseButtonMessage
    | ScrollMessage
    | KeyboardMessage
    | WindowResizeMessage
    | QuitMessage
    | TickMessage
    | SaveCompletedMessage
)

