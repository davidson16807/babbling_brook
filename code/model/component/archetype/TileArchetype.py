# HUMAN VETTED

from dataclasses import dataclass
from math import isnan


@dataclass(frozen=True)
class TileArchetype:
    top_texture: str
    side_texture: str
    # Zero is flat; infinity allows unlimited erosion. Heights use world units.
    max_erosion: float = 0.0
    is_collidable: bool = True
    has_detritus: bool = False
    is_moist: bool = False
    is_disturbed: bool = False

    def __post_init__(self):
        if isnan(self.max_erosion) or self.max_erosion < 0:
            raise ValueError("max_erosion must be nonnegative")
