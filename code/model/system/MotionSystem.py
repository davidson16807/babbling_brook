# HUMAN WRITTEN

"""Traverse XY waypoint lists at a constant horizontal speed."""
from dataclasses import replace
from math import isfinite, floor

from pyglm import glm

class MotionSystem:
    def __init__(self, seconds_per_tile: float):
        self.seconds_per_tile = seconds_per_tile

    def step(self, placements, motions, seconds):
        for entity, path in list(motions.items()):
            fraction = seconds / self.seconds_per_tile
            pair_id = int(floor(fraction))
            pairs = zipped(path, [*path[1:], path[-1]])
            if pair_id >= len(pairs): return path[-1]
            a,b = pairs[pair_id]
            placement = placements[entity]
            xy = glm.mix(a, b, fraction - pair_id)
            placements[entity] = replace(placement, position=glm.vec3(xy, placement.position.z))
