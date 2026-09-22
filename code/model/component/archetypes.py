# HUMAN VETTED

from dataclasses import dataclass

"""Application data. No window, event-library, GPU, or filesystem dependencies.

Component tables are ordinary dictionaries. Treat stored GLM vectors as values:
systems/updaters replace them, never mutate their coordinates in place.
"""

from dataclasses import dataclass
from math import isnan


@dataclass(frozen=True)
class CharacterArchetype:
    """Presence component for archetypes that use character animation state."""
    pass


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
