"""Translate pressed directional keys into camera-relative input axes."""

from pyglm import glm


class DirectionalKeysUpdater:
    def __init__(self, up, left, down, right, speed):
        self.up = up
        self.left = left
        self.down = down
        self.right = right
        self.speed = glm.vec2(speed)

    def update(self, pressed_keys: frozenset[str]) -> glm.vec2:
        return self.speed * glm.vec2(
            int(self.right in pressed_keys) - int(self.left in pressed_keys),
            int(self.up in pressed_keys) - int(self.down in pressed_keys),
        )
