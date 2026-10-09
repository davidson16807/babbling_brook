# HUMAN VETTED

from dataclasses import dataclass, field

from pyglm import glm

from ..Bounds import Bounds


@dataclass(frozen=True)
class BoxArchetype:
    """Shared material, dimensions, collision setting, and action for a kind of box."""
    top_texture: str
    side_texture: str
    scale: glm.vec3 = field(default_factory=lambda: glm.vec3(1))
    is_collidable: bool = True
    action: str = ""

    def bounds(self, position):
        """World bounds at a placement's bottom-center."""
        return Bounds(position - glm.vec3(self.scale.xy * .5, 0),
                      position + glm.vec3(self.scale.xy * .5, self.scale.z))
