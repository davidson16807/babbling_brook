# HUMAN VETTED

from dataclasses import dataclass


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
