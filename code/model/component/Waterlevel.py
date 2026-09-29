from dataclasses import dataclass


@dataclass(frozen=True)
class Waterlevel:
    map: str
    high_tide_liquid_level: float
    low_tide_liquid_level: float
    liquid_id: str | None = None
