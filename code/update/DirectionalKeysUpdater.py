"""Translate pressed directional keys into camera-relative input axes."""

from pyglm import glm


class DirectionalKeysUpdater:
    def __init__(self, up, left, down, right, magnitude=1):
        self.up = up
        self.left = left
        self.down = down
        self.right = right
        self.magnitude = glm.vec2(magnitude)

    def update(self, pressed_keys: frozenset[str]) -> glm.vec2:
        return self.magnitude * glm.vec2(
            int(self.right in pressed_keys) - int(self.left in pressed_keys),
            int(self.up in pressed_keys) - int(self.down in pressed_keys),
        )
