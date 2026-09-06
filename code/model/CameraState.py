from dataclasses import dataclass
from math import atan, pi, sqrt


@dataclass(frozen=True)
class CameraState:
    # The unsnapped angle accumulates small drags between displayed orientations.
    raw_azimuth: float = pi / 4
    look_azimuth: float = pi / 4
    elevation: float = atan(1 / sqrt(2))
    orthographic_scale: float = 12.0
