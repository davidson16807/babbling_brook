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
    animal_friend: bool = False
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
    windswept: bool = False
    waterswept: bool = False
    disturbed: bool = False

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


@dataclass(frozen=True)
class AnimalArchetype:
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


@dataclass(frozen=True)
class Liquid:
    top_texture1: str
    top_texture2: str
    freezing_temperature: float
    frozen_texture: str
    viscosity: float
    unpassable: bool = False


@dataclass(frozen=True)
class Waypoint:
    name: str
    in_game_texture: str
    in_editor_texture: str
    is_door: bool = False
