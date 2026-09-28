"""A periodic phase, with period measured in seconds."""
from dataclasses import dataclass, replace
from math import isfinite


@dataclass(frozen=True)
class Cycle:
    phase: float
    period: float

    def __add__(self, offset: float):
        return replace(self, phase=(self.phase + offset) % 1.0)
