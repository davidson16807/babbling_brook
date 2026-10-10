"""Backend-independent, absolutely positioned UI boxes, in viewport pixels.

Unlike `UiPanel`, which stacks text panels by anchor, a `UiBox` is placed by
its caller, so layouts can position chips, cells, and buttons themselves.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class UiBoxStyle:
    background: tuple[int, int, int, int]
    border: tuple[int, int, int, int]
    border_width: int = 1
    text_color: tuple[int, int, int] = (239, 241, 223)
    font_size: int = 22


@dataclass(frozen=True)
class UiBox:
    """Text, if any, is centered in the box and is not wrapped."""
    rect: tuple[int, int, int, int]  # left, top, width, height
    style: UiBoxStyle
    text: str = ''
