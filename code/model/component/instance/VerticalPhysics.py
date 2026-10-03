# HUMAN VETTED

from dataclasses import dataclass


@dataclass(frozen=True)
class VerticalPhysics:
    vertical_velocity: float
    is_grounded: bool
