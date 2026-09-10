from dataclasses import dataclass
from math import sin, cos, atan, pi, sqrt, floor

import glm

@dataclass(frozen=True)
class CameraState:
    # The unsnapped angle accumulates small drags between displayed orientations.
    raw_azimuth: float = pi/4
    elevation: float = atan(0.5)
    orthographic_scale: float = 12.0

    def look_azimuth(self):
        return (
            (pi/4 + floor((self.raw_azimuth - pi/4) / (pi/2) + .5) * pi/2)
             % (2*pi)
        )

    def direction_to(self):
        azimuth = self.look_azimuth()
        return glm.vec3(
            cos(self.elevation) * cos(azimuth),
            cos(self.elevation) * sin(azimuth), 
            sin(self.elevation)
        )

    def right(self):
        azimuth = self.look_azimuth()
        return glm.vec3(-sin(azimuth), cos(azimuth), 0)

    def forward(self):
        return -self.direction_to()
