
from math import floor
from pyglm import glm


I = glm.vec2(1,0)
J = glm.vec2(0,1)

class CollisionQuery:
    """Resolve one horizontal move against terrain and nearby one-tile objects."""

    def move(self, entity, origin, offset, placements, objects, map_):
        height_precision = 0.1
        moving = objects[placements[entity].archetype]
        # Axis separation permits sliding along obstacles. Callers use fixed small steps.
        for axis in (I+J,I,J):
            step = origin + glm.vec3(offset*axis, 0.0)
            bottom = step.z
            top = step.z + moving.height
            step2 = step.xy
            # disregard step if it falls off the map
            if not (0 <= step.x < map_.dimensions.x 
                and 0 <= step.y < map_.dimensions.y): continue 
            if   (map_.tile((floor(step.x), floor(step.y))).is_collidable 
              and bottom < map_.height(step2) - height_precision) : continue
            neighbors = [
                (key, objects[placement.archetype], placement.position)
                for key, placement in placements.items() if key != entity
            ]
            collisions = [
                (key, occupant, occupied)
                for key, occupant, occupied in neighbors
                if occupant.is_collidable
                and glm.distance(step2, glm.vec2(occupied)) < moving.radius + occupant.radius
                and not (top <= occupied.z or occupied.z + occupant.height <= bottom)
            ]
            if any(collisions): continue
            return step
        return origin
