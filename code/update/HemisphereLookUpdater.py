# HUMAN VETTED

from pyglm import glm
from ..messages import MouseMotionMessage

class HemisphereLookUpdater:
    def update(self, message) -> glm.vec2:
        if isinstance(message, MouseMotionMessage):
            return -message.offset * .01
        return glm.vec2(0)
