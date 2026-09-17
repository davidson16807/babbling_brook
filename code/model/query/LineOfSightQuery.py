"""Ray-marched visibility using map heights and existing object components."""
from math import ceil, floor, isfinite

from pyglm import glm


class LineOfSightQuery:
    def __init__(self, step_length: float):
        if not isfinite(step_length) or step_length <= 0:
            raise ValueError("step_length must be finite and positive")
        self.step_length = step_length

    def is_clear(self, source, target, placements, objects, map_, disabled=(), excluded=()):
        """Test a ray against terrain plus the tallest collidable object on each tile.

        Source and target are world positions (including sight/aim height).
        Callers pass disabled unit IDs and source/target IDs to exclude. This
        keeps game-specific unit conditions out of the shared query. Disabled
        units add zero height. Billboard height comes from ObjectArchetype.
        """
        if not all(isfinite(value) for value in (*source, *target)):
            raise ValueError("Sight endpoints must be finite")
        if source.xy not in map_ or target.xy not in map_:
            return False
        heights = {}
        for entity, placement in placements.items():
            if entity in disabled or entity in excluded:
                continue
            definition = objects[placement.archetype]
            if definition.is_collidable:
                cell = floor(placement.position.x), floor(placement.position.y)
                heights[cell] = max(heights.get(cell, 0.0), definition.height)
        steps = max(2, ceil(glm.distance(source, target) / self.step_length))
        for step in range(steps + 1):
            point = glm.mix(source, target, step / steps)
            ground = map_.height(point.xy)
            cell = floor(point.x), floor(point.y)
            if ground is None or point.z < ground + heights.get(cell, 0.0):
                return False
        return True
