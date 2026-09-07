from dataclasses import replace
from math import cos, sin
from pyglm import glm


class MovementSystem:
    def __init__(self, collisions):
        self.collisions = collisions

    def step(self, positions, archetyped, characters, objects, static_objects, map_, keys, azimuth, seconds):
        right = glm.vec2(-sin(azimuth), cos(azimuth))
        forward = glm.vec2(-cos(azimuth), -sin(azimuth))
        direction = right * (int('d' in keys) - int('a' in keys)) + forward * (int('w' in keys) - int('s' in keys))
        running = 'shift' in keys or 'right shift' in keys
        if glm.length(direction) > 0:
            direction = glm.normalize(direction)
        before = positions['player']
        after = self.collisions.move('player', before, direction * (4.0 if running else 2.5) * seconds,
            positions, archetyped, objects, static_objects, map_)
        moving = glm.distance(glm.vec2(before), glm.vec2(after)) > 1e-6
        state = characters['player']
        animation = ('running' if running else 'walking') if moving else 'standing'
        return ({**positions, 'player': after}, {**characters, 'player': replace(state,
            facing=direction if moving else state.facing, animation=animation,
            elapsed=state.elapsed if state.animation == animation else 0.0)})
