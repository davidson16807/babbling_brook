from dataclasses import dataclass


@dataclass(frozen=True)
class ZoneAdjacency:
    """A two-way connection between two zones through waypoints of one color code.

    Lookups index each adjacency twice, under (zone1, colorcode) and (zone2, colorcode).
    """
    zone1: str
    zone2: str
    colorcode: str
    preposition_to1: str = ''
    preposition_to2: str = ''
    key_to1: str | None = None
    key_to2: str | None = None
