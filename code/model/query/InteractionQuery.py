# HUMAN VETTED

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
            and objects[archetyped[entity]].action
        ]
        ranked = []
        for entity, archetype, position in candidates:
            offset = glm.vec2(position - origin)
            distance = glm.length(offset)
            if distance > 1.0: continue
            alignment = glm.dot(facing, offset / distance) if distance > 0 else 1.0
            ranked.append((distance - .2 * alignment, entity, archetype))
        return min(ranked, key=lambda item: item[0])[1:] if ranked else None
