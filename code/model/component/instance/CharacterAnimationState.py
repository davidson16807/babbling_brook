# HUMAN VETTED

from dataclasses import dataclass, field

from pyglm import glm


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
