from dataclasses import dataclass


@dataclass(frozen=True)
class ZoneDirections:
    north: str | None = None
    south: str | None = None
    east: str | None = None
    west: str | None = None
