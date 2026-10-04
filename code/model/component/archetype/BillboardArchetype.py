# HUMAN VETTED

from dataclasses import dataclass


@dataclass(frozen=True)
class BillboardArchetype:
    texture: str
    is_collidable: bool = True
    radius: float = 0.3
    height: float = 1.0
    width: float = 0.9
    has_gravity: bool = True
    action: str = ""
    lexeme: str = ""
