# HUMAN VETTED

from dataclasses import dataclass


@dataclass(frozen=True)
class SeasonalTileArchetype:
    default: str
    fallen_leaves: str
    dead_grass: str
    snowy: str
