from dataclasses import dataclass, field
from pyglm import glm


@dataclass(frozen=True)
class Landmark:
    map_id: int | str
    lexeme: str
    by_radius: float
    at_position: glm.vec3 = field(default_factory=lambda: glm.vec3(0))
    on_position: glm.vec3 = field(default_factory=lambda: glm.vec3(0))
    in_position: glm.vec3 = field(default_factory=lambda: glm.vec3(0))
    under_position: glm.vec3 = field(default_factory=lambda: glm.vec3(0))
    within_position: glm.vec3 = field(default_factory=lambda: glm.vec3(0))
    before_position: glm.vec3 = field(default_factory=lambda: glm.vec3(0))
    against_position: glm.vec3 = field(default_factory=lambda: glm.vec3(0))
