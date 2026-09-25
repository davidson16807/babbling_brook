# HUMAN VETTED

from dataclasses import dataclass
from math import sin, cos, atan, pi, sqrt, floor

import glm

@dataclass()
class CameraState:
    # The unsnapped angle accumulates small drags between displayed orientations.
    raw_azimuth: float = pi/4
    raw_elevation: float = pi/6
    look_azimuth: float = pi/4
    look_elevation: float = pi/6
    orthographic_scale: float = 12.0

    def right(self):
        azimuth = self.look_azimuth
        return glm.vec3(-sin(azimuth), cos(azimuth), 0)

    def forward(self):
        azimuth = self.look_azimuth
        return -glm.vec3(
            cos(self.look_elevation) * cos(azimuth),
            cos(self.look_elevation) * sin(azimuth),
            sin(self.look_elevation)
        )
