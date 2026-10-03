from dataclasses import dataclass


@dataclass(frozen=True)
class Zone:
    name: str
    map_filename: str
    biome: str
