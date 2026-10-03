# HUMAN VETTED

from dataclasses import replace

from pyglm import glm
from ..component.instance import VerticalPhysics


class GravitySystem:
    def __init__(self, gravity=16.0):
        self.gravity = gravity

    def step(self, placements, physics, map_, seconds, boxes=None, body_heights=None):
        placements, physics = dict(placements), dict(physics)
        for entity, state in physics.items():
            placement = placements[entity]
            position = placement.position
            ground = map_.height(glm.vec2(position))
            if ground is None:
                continue
            velocity = state.vertical_velocity - self.gravity * seconds
            height = position.z + velocity * seconds
            # Box tops support entities; undersides stop upward movement.
            for obstacle, box in (boxes or {}).items():
                if obstacle == entity:
                    continue
                if not (box.minimum.x <= position.x <= box.maximum.x
                        and box.minimum.y <= position.y <= box.maximum.y):
                    continue
                if velocity <= 0 and position.z >= box.maximum.z - 1e-5:
                    ground = max(ground, box.maximum.z)
                elif velocity > 0:
                    body_height = (body_heights or {}).get(entity, 0.0)
                    if position.z + body_height <= box.minimum.z + 1e-5 and height + body_height >= box.minimum.z:
                        height = box.minimum.z - body_height
                        velocity = 0.0
            grounded = height <= ground and velocity <= 0
            placements[entity] = replace(
                placement,
                position=glm.vec3(position.x, position.y, ground if grounded else height),
            )
            physics[entity] = VerticalPhysics(0.0 if grounded else velocity, grounded)
        return placements, physics
