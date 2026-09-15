# HUMAN VETTED

"""Structured draw inputs. No GL objects or entity IDs cross this interface."""
from dataclasses import dataclass

from pyglm import glm


@dataclass(frozen=True)
class ViewState:
    clip_from_world: glm.mat4
    camera_right: glm.vec3

