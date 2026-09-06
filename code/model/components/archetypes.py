# HUMAN VETTED

from collections import defaultdict
from dataclasses import dataclass
from typing import TypeAlias

from pyglm import glm

"""Application data. No window, event-library, GPU, or filesystem dependencies.

Component tables are ordinary dictionaries. Treat stored GLM vectors as values:
systems/updaters replace them, never mutate their coordinates in place.
"""

# COMPONENTS

@dataclass(frozen=True)
class CharacterAnimation:
    # 0 faces toward the camera, 1 away. Rightward poses mirror the UVs.
    directions: tuple[DirectionFrames, DirectionFrames]
    seconds_per_frame: float = 0.3

@dataclass(frozen=True)
class CharacterArchetype:
    standing: CharacterAnimation
    walking: CharacterAnimation | None = None
    running: CharacterAnimation | None = None


@dataclass(frozen=True)
class TileArchetype:
    texture: str
    show_exposed_sides: bool = True
    is_smooth: bool = False
    is_collidable: bool = True


@dataclass(frozen=True)
class ObjectArchetype:
    texture: str
    is_static: bool = False
    is_collidable: bool = True
    radius: float = 0.3
    height: float = 1.0
    width: float = 0.9
    has_gravity: bool = True
    action: str = ""
    label: str = "Object"
