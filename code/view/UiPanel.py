"""Backend-independent descriptions of text panels, in viewport pixels."""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class UiText:
    text: str
    font_size: int
    line_height: int
    color: tuple[int, int, int]


@dataclass(frozen=True)
class UiPanel:
    """Panels sharing an anchor stack inward in sequence, separated by gap.

    Width is capped by the viewport minus horizontal margins; None fills it.
    Padding is (left, top, right, bottom). Text styles apply to all wrapped lines.
    """
    lines: tuple[UiText, ...]
    width: int | None
    background: tuple[int, int, int, int]
    border: tuple[int, int, int, int]
    padding: tuple[int, int, int, int]
    anchor: Literal['top-left', 'bottom-left'] = 'top-left'
    margin: tuple[int, int] = (16, 16)
    gap: int = 12
