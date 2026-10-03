from dataclasses import dataclass


@dataclass(frozen=True)
class ZoneAdjacency:
    preposition_to1: str = ''
    preposition_to2: str = ''
    key_to1: str | None = None
    key_to2: str | None = None
