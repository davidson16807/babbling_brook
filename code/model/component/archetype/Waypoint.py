from dataclasses import dataclass


@dataclass(frozen=True)
class Waypoint:
    colorcode: str
    door: bool = False
