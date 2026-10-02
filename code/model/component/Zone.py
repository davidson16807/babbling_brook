"""World metadata. Zone connectivity is data; it does not trigger travel."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Biome:
    summer_temperature: float
    winter_temperature: float
    leaf_state: int = 1
    grass_state: int = 1
    is_snowy: bool = False


@dataclass(frozen=True)
class Zone:
    name: str
    map_filename: str
    biome: str


@dataclass(frozen=True)
class ZoneDirections:
    north: str | None = None
    south: str | None = None
    east: str | None = None
    west: str | None = None


@dataclass(frozen=True)
class ZoneAdjacency:
    preposition_to1: str = ''
    preposition_to2: str = ''
    key_to1: str | None = None
    key_to2: str | None = None

