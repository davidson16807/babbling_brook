from dataclasses import dataclass


@dataclass(frozen=True)
class Waterlevel:
    high_tide_liquid_level: float
    low_tide_liquid_level: float
    liquid: str | None = None
