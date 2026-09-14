# HUMAN VETTED

from math import floor
from pyglm import glm


class InteractionQuery:
    def nearest(self, origin, facing, placements, objects):
        candidates = [
            (entity, objects[placement.archetype], placement.position)
            for entity, placement in placements.items()
            if entity != 'player'
            and placement.archetype in objects
            and objects[placement.archetype].action
        ]
        ranked = []
        for entity, archetype, position in candidates:
            offset = glm.vec2(position - origin)
            distance = glm.length(offset)
            if distance > 1.0: continue
            alignment = glm.dot(facing, offset / distance) if distance > 0 else 1.0
            ranked.append((distance - .2 * alignment, entity, archetype))
        return min(ranked, key=lambda item: item[0])[1:] if ranked else None
