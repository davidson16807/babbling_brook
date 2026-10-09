# HUMAN VETTED

"""Ray-marched visibility using map heights and existing object components."""
from math import ceil, floor, isfinite

from pyglm import glm


class LineOfSightQuery:
    def __init__(self, step_length: float):
        self.step_length = step_length

    def is_clear(self, source, target, placements, objects, map_, disabled=(), excluded=()):
        # USAGE NOTE: excluded should include source and target entities
        # Only placements whose archetype has a component in `objects` occlude.
        heights = {}
        for entity, placement in placements.items():
            if entity in disabled or entity in excluded: continue
            if placement.archetype not in objects: continue
            object_ = objects[placement.archetype]
            if object_.is_collidable:
                cell = floor(placement.position.x), floor(placement.position.y)
                heights[cell] = max(heights.get(cell, 0.0), object_.height)
        step_count = max(2, ceil(glm.distance(source, target) / self.step_length))
        for step_id in range(step_count+1):
            step = glm.mix(source, target, step_id / step_count)
            ground = map_.height(step.xy)
            cell = floor(step.x), floor(step.y)
            if ground is None or step.z < ground + heights.get(cell, 0.0):
                return False
        return True
