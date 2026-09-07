from math import floor
from pyglm import glm


class InteractionQuery:
    def nearest(self, origin, facing, positions, archetyped, objects, static_objects):
        candidates = [(entity, archetyped[entity], pos) for entity, pos in positions.items() if entity != 'player']
        candidates += [(entity, p.archetype, p.position) for entity, p in static_objects.items()]
        ranked = []
        for entity, key, position in candidates:
            if not objects[key].action or abs(position.z - origin.z) > 1.0:
                continue
            if abs(floor(position.x) - floor(origin.x)) > 1 or abs(floor(position.y) - floor(origin.y)) > 1:
                continue
            delta = glm.vec2(position - origin)
            distance = glm.length(delta)
            if distance <= 1.5:
                alignment = glm.dot(facing, delta / distance) if distance > 0 else 1.0
                ranked.append((distance - .2 * alignment, entity, key))
        return min(ranked, key=lambda item: item[0])[1:] if ranked else None
