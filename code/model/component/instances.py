# HUMAN VETTED

"""Model data. No window, event-library, GPU, or filesystem dependencies.

Component tables are ordinary dictionaries. Treat stored GLM vectors as values:
systems/updaters replace them, never mutate their coordinates in place.
"""

from dataclasses import dataclass, field
from math import isfinite
from pyglm import glm

from ..identifiers import ArchetypeId
from ..MotionSegment import MotionSegment

# COMPONENTS

@dataclass(frozen=True)
class VerticalPhysics:
    vertical_velocity: float
    is_grounded: bool

@dataclass(frozen=True)
class ObjectPlacement:
    archetype: ArchetypeId
    position: glm.vec3

@dataclass(frozen=True)
class CharacterAnimationState:
    facing: glm.vec2 = field(default_factory=lambda: glm.vec2(0, 1))
    animation: str = "standing"
    elapsed: float = 0.0


@dataclass(frozen=True)
class Motion:
    segments: tuple[MotionSegment, ...]
    segment_index: int = 0
    elapsed: float = 0.0

    def __post_init__(self):
        if not 0 <= self.segment_index <= len(self.segments):
            raise ValueError("Invalid motion segment index")
        if not isfinite(self.elapsed) or self.elapsed < 0:
            raise ValueError("Motion elapsed time must be finite and nonnegative")
        if self.segment_index < len(self.segments) and self.elapsed > self.segments[self.segment_index].duration:
            raise ValueError("Elapsed time exceeds the current segment duration")
