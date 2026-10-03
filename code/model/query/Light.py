from dataclasses import dataclass, field

from pyglm import glm


@dataclass(frozen=True)
class Light:
    direction: glm.dvec3 = field(default_factory=lambda: glm.dvec3(-.5, -.7, 1))
    color: glm.dvec3 = field(default_factory=lambda: glm.dvec3(1))
    background: glm.dvec3 = field(default_factory=lambda: glm.dvec3(.16, .23, .25))
