from dataclasses import replace
from math import cos, sin
from pyglm import glm

from ..messages import TickMessage


class MovementUpdater:
    def __init__(self, collisions):
        self.collisions = collisions

    def update(self, model, message):
        if not isinstance(message, TickMessage):
            return model
        instances = model.instances
        positions = instances.positionables
        archetyped = instances.archetyped
        characters = instances.characters
        objects = model.archetypes.objects
        static_objects = model.map.static_objects
        map_ = model.map
        keys = model.controls.pressed_keys
        azimuth = model.camera.look_azimuth
        seconds = message.seconds
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
        positions = {**positions, 'player': after}
        characters = {**characters, 'player': replace(state,
            facing=direction if moving else state.facing, animation=animation,
            elapsed=state.elapsed if state.animation == animation else 0.0)}
        return replace(model, instances=replace(instances, positionables=positions, characters=characters))
