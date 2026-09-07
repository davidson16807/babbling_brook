from pyglm import glm
from ..components.instances import VerticalPhysics


class GravitySystem:
    def __init__(self, gravity=16.0):
        self.gravity = gravity

    def step(self, positions, physics, map_, seconds):
        positions, physics = dict(positions), dict(physics)
        for entity, state in physics.items():
            position = positions[entity]
            ground = map_.height(glm.vec2(position))
            if ground is None:
                continue
            velocity = state.vertical_velocity - self.gravity * seconds
            height = position.z + velocity * seconds
            grounded = height <= ground and velocity <= 0
            positions[entity] = glm.vec3(position.x, position.y, ground if grounded else height)
            physics[entity] = VerticalPhysics(0.0 if grounded else velocity, grounded)
        return positions, physics
