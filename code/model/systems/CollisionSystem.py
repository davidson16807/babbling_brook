from math import floor
from pyglm import glm


class CollisionSystem:
    """Resolve one horizontal move against terrain and nearby one-tile objects."""

    def move(self, entity, origin, offset, positions, archetyped, objects, static_objects, map_):
        definition = objects[archetyped[entity]]
        result = glm.vec3(origin)
        # Axis separation permits sliding along obstacles. Callers use fixed small steps.
        for axis in (0, 1):
            candidate = glm.vec3(result)
            candidate[axis] += offset[axis]
            p = glm.vec2(candidate)
            radius = definition.radius
            if not (radius <= p.x < map_.dimensions.x - radius and radius <= p.y < map_.dimensions.y - radius):
                continue
            ground = map_.height(p)
            tile = map_.archetype((floor(p.x), floor(p.y)))
            if not tile.is_collidable or ground > candidate.z + .10:
                continue
            blocked = False
            neighbors = [(other, archetyped[other], pos) for other, pos in positions.items() if other != entity]
            neighbors += [(other, item.archetype, item.position) for other, item in static_objects.items()]
            for other, key, position in neighbors:
                if abs(floor(position.x) - floor(p.x)) > 1 or abs(floor(position.y) - floor(p.y)) > 1:
                    continue
                obstacle = objects[key]
                if not definition.is_collidable or not obstacle.is_collidable:
                    continue
                if candidate.z >= position.z + obstacle.height or candidate.z + definition.height <= position.z:
                    continue
                if glm.distance(p, glm.vec2(position)) < radius + obstacle.radius:
                    blocked = True
                    break
            if not blocked:
                result = candidate
        return result
