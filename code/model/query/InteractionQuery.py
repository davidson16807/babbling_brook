from math import floor
from pyglm import glm


class InteractionQuery:
    def nearest(self, origin, facing, positions, archetyped, objects):
        candidates = [
            (entity, objects[archetyped[entity]], position) 
            for entity, position in positions.items() 
            if entity != 'player'
            and entity in archetyped
            and archetyped[entity] in objects
        ]
        ranked = []
        for entity, archetype, position in candidates:
            if not archetype.action or abs(position.z - origin.z) > 1.0:
                continue
            if abs(floor(position.x) - floor(origin.x)) > 1 or abs(floor(position.y) - floor(origin.y)) > 1:
                continue
            delta = glm.vec2(position - origin)
            distance = glm.length(delta)
            if distance <= 1.5:
                alignment = glm.dot(facing, delta / distance) if distance > 0 else 1.0
                ranked.append((distance - .2 * alignment, entity, archetype))
        return min(ranked, key=lambda item: item[0])[1:] if ranked else None
