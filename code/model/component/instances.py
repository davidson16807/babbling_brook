# HUMAN VETTED

"""Model data. No window, event-library, GPU, or filesystem dependencies.

Component tables are ordinary dictionaries. Treat stored GLM vectors as values:
systems/updaters replace them, never mutate their coordinates in place.
"""

from dataclasses import dataclass, field
from pyglm import glm

from ..identifiers import ArchetypeId

# COMPONENTS

@dataclass(frozen=True)
class VerticalPhysics:
    vertical_velocity: float
    is_grounded: bool

@dataclass(frozen=True)
class BillboardPlacement:
    archetype: ArchetypeId
    position: glm.vec3

@dataclass(frozen=True)
class BoxPlacement:
    """A tile-material box positioned at its bottom-center, sized in world units."""
    archetype: ArchetypeId
    position: glm.vec3
    scale: glm.vec3 = field(default_factory=lambda: glm.vec3(1))

    @property
    def minimum(self):
        return self.position - glm.vec3(self.scale.xy * .5, 0)

    @property
    def maximum(self):
        return self.position + glm.vec3(self.scale.xy * .5, self.scale.z)

@dataclass(frozen=True)
class CharacterAnimationState:
    facing: glm.vec2 = field(default_factory=lambda: glm.vec2(0, 1))
    animation: str = "standing"
    elapsed: float = 0.0
    hurt: bool = False
    tired: bool = False
    asleep: bool = False
    hot: bool = False
    cold: bool = False
    angry: bool = False
    sad: bool = False
    afraid: bool = False
    happy: bool = False
