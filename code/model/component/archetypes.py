# HUMAN VETTED

from collections import defaultdict
from dataclasses import dataclass
from typing import TypeAlias

from pyglm import glm

"""Application data. No window, event-library, GPU, or filesystem dependencies.

Component tables are ordinary dictionaries. Treat stored GLM vectors as values:
systems/updaters replace them, never mutate their coordinates in place.
"""

from dataclasses import dataclass
from math import isnan

# COMPONENTS

@dataclass(frozen=True)
class DirectionFrames:
    textures: tuple[str, str]

@dataclass(frozen=True)
class CharacterAnimation:
    # 0 faces toward the camera, 1 away. Rightward poses mirror the UVs.
    directions: tuple[DirectionFrames, DirectionFrames]
    seconds_per_frame: float = 0.3

@dataclass(frozen=True)
class CharacterArchetype:
    animations: dict[str, CharacterAnimation]

    def __post_init__(self):
        if 'standing' not in self.animations:
            raise ValueError("A character requires a standing animation")


@dataclass(frozen=True)
class TileArchetype:
    top_texture: str
    side_texture: str
    # Zero is flat; infinity allows unlimited erosion. Heights use world units.
    max_erosion: float = 0.0
    is_collidable: bool = True

    def __post_init__(self):
        if isnan(self.max_erosion) or self.max_erosion < 0:
            raise ValueError("max_erosion must be nonnegative")


@dataclass(frozen=True)
class ObjectArchetype:
    texture: str
    is_collidable: bool = True
    radius: float = 0.3
    height: float = 1.0
    width: float = 0.9
    has_gravity: bool = True
    action: str = ""
    label: str = "Object"
