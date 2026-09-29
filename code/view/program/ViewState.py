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

