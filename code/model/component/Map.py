"""Map metadata, separate from the terrain surface in model.Map."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Map:
    name: str
    filename: str
    north_map_id: int | None = None
    south_map_id: int | None = None
    east_map_id: int | None = None
    west_map_id: int | None = None
    summer_temperature: float = 20.0
    winter_temperature: float = 0.0
    wild: bool = False
    leaf_state: int = 1
    grass_state: int = 1
    snowy: bool = False
