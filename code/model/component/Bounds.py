"""Derived world-space bounds, shared by collision and gravity queries."""
from dataclasses import dataclass
from pyglm import glm


@dataclass(frozen=True)
class Bounds:
    minimum: glm.vec3
    maximum: glm.vec3
