# HUMAN VETTED

"""Model data. No window, event-library, GPU, or filesystem dependencies.

Component tables are ordinary dictionaries. Treat stored GLM vectors as values:
systems/updaters replace them, never mutate their coordinates in place.
"""

from dataclasses import dataclass, field
from math import isfinite, sqrt
from pyglm import glm

from ..identifiers import ArchetypeId

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
class MotionSegment:
    """Linear horizontal travel with an unclamped quadratic height function."""

    start: glm.vec2
    end: glm.vec2
    height_coefficients: tuple[float, float, float]
    duration: float

    def __post_init__(self):
        if len(self.height_coefficients) != 3:
            raise ValueError("height_coefficients must contain quadratic, linear, and constant values")
        values = (*self.start, *self.end, *self.height_coefficients, self.duration)
        if not all(isfinite(value) for value in values):
            raise ValueError("Motion segment values must be finite")
        if self.duration <= 0:
            raise ValueError("Motion segment duration must be positive")

    def __call__(self, time: float) -> glm.vec3:
        progress = time / self.duration
        xy = self.start + (self.end - self.start) * progress
        quadratic, linear, constant = self.height_coefficients
        height = quadratic * time * time + linear * time + constant
        return glm.vec3(xy, height)

def linear_height_coefficients(
        start_height: float,
        end_height: float,
        duration: float) -> tuple[float, float, float]:
    """Return coefficients for linear interpolation between two heights."""

    if not all(isfinite(value) for value in (start_height, end_height, duration)):
        raise ValueError("Height premises must be finite")
    if duration <= 0:
        raise ValueError("duration must be positive")
    return 0.0, (end_height - start_height) / duration, start_height

def arc_height_coefficients(
        start_height: float,
        end_height: float,
        maximum_height: float,
        duration: float) -> tuple[float, float, float]:
    """Return a downward parabola through both endpoints with the given maximum."""

    values = start_height, end_height, maximum_height, duration
    if not all(isfinite(value) for value in values):
        raise ValueError("Height premises must be finite")
    if duration <= 0:
        raise ValueError("duration must be positive")
    if maximum_height < max(start_height, end_height):
        raise ValueError("maximum_height cannot be below either endpoint")
    if maximum_height == start_height == end_height:
        return 0.0, 0.0, start_height

    start_root = sqrt(maximum_height - start_height)
    end_root = sqrt(maximum_height - end_height)
    root_sum = start_root + end_root
    curvature = (root_sum / duration) ** 2
    vertex_time = duration * start_root / root_sum
    return -curvature, 2 * curvature * vertex_time, start_height

@dataclass(frozen=True)
class Motion:
    segments: tuple[MotionSegment, ...]
    segment_index: int = 0
    elapsed: float = 0.0

    def __post_init__(self):
        if not self.segments:
            raise ValueError("Motion requires at least one segment")
        if not 0 <= self.segment_index < len(self.segments):
            raise ValueError("segment_index is outside the motion")
        duration = self.segments[self.segment_index].duration
        if not isfinite(self.elapsed) or not 0 <= self.elapsed <= duration:
            raise ValueError("elapsed is outside the current segment")
