"""Translate pressed directional keys into camera-relative input axes."""

from pyglm import glm


class DirectionalKeysUpdater:
    def update(self, pressed_keys: frozenset[str]) -> glm.vec2:
        return glm.vec2(
            int('d' in pressed_keys) - int('a' in pressed_keys),
            int('w' in pressed_keys) - int('s' in pressed_keys),
        )
