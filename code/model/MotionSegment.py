# HUMAN VETTED

"""Time-parametric motion. Terrain constraints belong to MotionSystem."""
from dataclasses import dataclass
from math import isfinite, sqrt

from pyglm import glm


def linear_height(start_z: float, end_z: float, duration: float) -> tuple[float, float, float]:
    return 0.0, (end_z - start_z) / duration, start_z

def arc_height(start_z: float, end_z: float, maximum_z: float, duration: float) -> tuple[float, float, float]:
    """Quadratic with the requested maximum on [0, duration], including endpoints.

    Endpoint maxima give the degenerate rising/falling arcs. Equal endpoint and
    maximum heights give a constant polynomial; there is no separate fall mode.
    """
    rise, fall = sqrt(maximum_z - start_z), sqrt(maximum_z - end_z)
    rate = (rise + fall) / duration
    return -rate * rate, 2 * rise * rate, start_z

@dataclass(frozen=True)
class MotionSegment:
    start: glm.vec2
    end: glm.vec2
    height_coefficients: tuple[float, float, float]
    duration: float

    def __call__(self, time: float) -> glm.vec3:
        """Evaluate raw motion; the caller supplies a time in [0, duration]."""
        xy = glm.mix(self.start, self.end, time / self.duration)
        a, b, c = self.height_coefficients
        return glm.vec3(xy, (a * time + b) * time + c)
