# HUMAN VETTED

"""Structured draw inputs. No GL objects or entity IDs cross this interface."""
from dataclasses import dataclass, field

from pyglm import glm


@dataclass(frozen=True)
class ViewState:
    clip_from_world: glm.mat4
    camera_right: glm.vec3
    light_direction: glm.vec3 = field(default_factory=lambda: glm.vec3(-.5, -.7, 1))
    light_color: glm.vec3 = field(default_factory=lambda: glm.vec3(1))
    camera_position: glm.vec3 = field(default_factory=lambda: glm.vec3(0))
    # (scale height in metres, effective RGB surface coefficient per metre).
    # First Rayleigh, then Mie, matching LightQuery's phase weights.
    scatterers: tuple[tuple[float, glm.vec3], ...] = ()
    # Supply the forward direction for parallel orthographic rays. None uses
    # perspective rays originating at camera_position.
    camera_forward: glm.vec3 | None = None
