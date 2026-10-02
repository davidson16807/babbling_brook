from dataclasses import dataclass


@dataclass(frozen=True)
class Waypoint:
    colorcode: str
    door: bool = False


@dataclass(frozen=True)
class CardinalWaypoint:
    name: str
    texture: str
    direction: str
    colorcode: str
