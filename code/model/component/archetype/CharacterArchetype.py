# HUMAN VETTED

from dataclasses import dataclass


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
