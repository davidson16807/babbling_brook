# HUMAN VETTED

from dataclasses import dataclass

"""Application data. No window, event-library, GPU, or filesystem dependencies.

Component tables are ordinary dictionaries. Treat stored GLM vectors as values:
systems/updaters replace them, never mutate their coordinates in place.
"""

from dataclasses import dataclass, field
from math import isfinite, isnan
from pyglm import glm

from .Bounds import Bounds


@dataclass(frozen=True)
class CharacterArchetype:
    """Character traits; their behavioral systems are not yet implemented."""
    male: bool = False
    lifestage: int = 1
    skin: int = 3
    hair: int = 3
    bald_prone: bool = False
    dwarf: bool = False
    strong: bool = False
    fat: bool = False
    attractive: bool = False
    hungry: bool = False
    thirsty: bool = False
    wants: str = ''
    loves: str = ''
    harasses: str = ''
    follows: str = ''
    avoids: str = ''
    guards: str = ''
    wanders: bool = False
    run_speed: float = 2.0
    swim_speed: float = 0.0
    climb_speed: float = 0.0
    colorblind: bool = False
    deaf: bool = False
    blind: bool = False
    speaks_native: bool = False
    speaks_foreign: bool = False
    numeracy: int = 1
    literacy: int = 0
    places_known: int = 0
    people_known: int = 0
    respect_level: int = 1
    respects_level: int = 1
    wealth_level: int = 1
    heals: bool = False
    mends: bool = False
    cooks: bool = False
    smiths: bool = False
    carpents: bool = False
    masons: bool = False
    picks_locks: bool = False
    controls_weather: bool = False
    creature_friend: bool = False
    owes_player: bool = False
    unescortable: bool = False
    criminal: bool = False


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


@dataclass(frozen=True)
class BoxArchetype:
    """Shared material, dimensions, and collision setting for a kind of box."""
    top_texture: str
    side_texture: str
    scale: glm.vec3 = field(default_factory=lambda: glm.vec3(1))
    is_collidable: bool = True

    def bounds(self, position):
        """World bounds at a placement's bottom-center."""
        return Bounds(position - glm.vec3(self.scale.xy * .5, 0),
                      position + glm.vec3(self.scale.xy * .5, self.scale.z))


@dataclass(frozen=True)
class BillboardArchetype:
    texture: str
    is_collidable: bool = True
    radius: float = 0.3
    height: float = 1.0
    width: float = 0.9
    has_gravity: bool = True
    action: str = ""
    label: str = "Object"
    lexeme: str = ""


@dataclass(frozen=True)
class CreatureArchetype:
    run_speed: float = 0.0
    swim_speed: float = 0.0
    climb_speed: float = 0.0
    warm_blooded: bool = False
    colorblind: bool = False
    uv_vision: bool = False
    heat_vision: bool = False
    forages: bool = False
    hunts_alone: bool = False
    pack_hunts: bool = False
    eats_berries: bool = False
    eats_grass: bool = False
    eats_small_game: bool = False
    eats_big_game: bool = False
    fly_speed: float = 0.0
    eats_seeds: bool = False
    eats_fish: bool = False


@dataclass(frozen=True)
class Liquid:
    top_texture1: str
    top_texture2: str
    freezing_temperature: float
    frozen_texture: str
    viscosity: float
    is_unpassable: bool = False
    side_texture: str = ""


@dataclass(frozen=True)
class SeasonalTileArchetype:
    default: str
    fallen_leaves: str
    dead_grass: str
    snowy: str
