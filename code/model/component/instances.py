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
    """A box archetype instance positioned at its bottom-center."""
    archetype: ArchetypeId
    position: glm.vec3

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
