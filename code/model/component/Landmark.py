from dataclasses import dataclass, field
from pyglm import glm


@dataclass(frozen=True)
class Landmark:
    map_id: int
    lexeme: str
    by_radius: float
    at_point: glm.vec3 = field(default_factory=lambda: glm.vec3(0))
    on_point: glm.vec3 = field(default_factory=lambda: glm.vec3(0))
    in_point: glm.vec3 = field(default_factory=lambda: glm.vec3(0))
    under_point: glm.vec3 = field(default_factory=lambda: glm.vec3(0))
    within_point: glm.vec3 = field(default_factory=lambda: glm.vec3(0))
    before_point: glm.vec3 = field(default_factory=lambda: glm.vec3(0))
    against_point: glm.vec3 = field(default_factory=lambda: glm.vec3(0))
