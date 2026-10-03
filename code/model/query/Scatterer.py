from dataclasses import dataclass

from pyglm import glm


@dataclass(frozen=True)
class Scatterer:
    atmosphere_scale_height: float
    rgb_surface_air_scattering_coefficient: glm.dvec3
