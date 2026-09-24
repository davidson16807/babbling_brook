# HUMAN VETTED

from dataclasses import dataclass
from math import sin, cos, pi

import glm

@dataclass()
class CameraState:
    azimuth: float = pi/4
    elevation: float = pi/6
    orthographic_scale: float = 12.0

    def right(self):
        azimuth = self.azimuth
        return glm.vec3(-sin(azimuth), cos(azimuth), 0)

    def forward(self):
        azimuth = self.azimuth
        return -glm.vec3(
            cos(self.elevation) * cos(azimuth),
            cos(self.elevation) * sin(azimuth), 
            sin(self.elevation)
        )
