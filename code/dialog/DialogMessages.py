"""Backend-neutral messages accepted by ``DialogUpdater``."""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PointerDown:
    position: tuple[int, int]


@dataclass(frozen=True, slots=True)
class PointerMove:
    position: tuple[int, int]


@dataclass(frozen=True, slots=True)
class PointerUp:
    position: tuple[int, int]


@dataclass(frozen=True, slots=True)
class KeyPress:
    key: str


@dataclass(frozen=True, slots=True)
class Resize:
    size: tuple[int, int]


@dataclass(frozen=True, slots=True)
class Quit:
    pass
