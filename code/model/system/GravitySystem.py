# HUMAN VETTED

from dataclasses import replace

from pyglm import glm
from ..component.instances import VerticalPhysics


class GravitySystem:
    def __init__(self, gravity=16.0):
        self.gravity = gravity

    def step(self, placements, physics, map_, seconds):
        placements, physics = dict(placements), dict(physics)
        for entity, state in physics.items():
            placement = placements[entity]
            position = placement.position
            ground = map_.height(glm.vec2(position))
            if ground is None:
                continue
            velocity = state.vertical_velocity - self.gravity * seconds
            height = position.z + velocity * seconds
            grounded = height <= ground and velocity <= 0
            placements[entity] = replace(
                placement,
                position=glm.vec3(position.x, position.y, ground if grounded else height),
            )
            physics[entity] = VerticalPhysics(0.0 if grounded else velocity, grounded)
        return placements, physics
