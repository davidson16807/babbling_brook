from dataclasses import dataclass


@dataclass(frozen=True)
class Biome:
    summer_temperature: float
    winter_temperature: float
    leaf_state: int = 1
    grass_state: int = 1
    is_snowy: bool = False
