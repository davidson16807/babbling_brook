"""Choose linear or jumping presentation for one adjacent-tile movement."""
from math import isfinite

from ..MotionSegment import MotionSegment, linear_height, arc_height


class TileMotionQuery:
    def __init__(self, seconds_per_tile: float, maximum_height_change: float):
        if not isfinite(seconds_per_tile) or seconds_per_tile <= 0:
            raise ValueError("seconds_per_tile must be finite and positive")
        if not isfinite(maximum_height_change) or maximum_height_change < 0:
            raise ValueError("maximum_height_change must be finite and nonnegative")
        self.seconds_per_tile = seconds_per_tile
        self.maximum_height_change = maximum_height_change

    def segment(self, source, destination, map_):
        """Return None for a forbidden cliff; occupancy and other rules are external."""
        continuous = map_.is_continuous_transition(source, destination)
        start, end = map_.world_position(source), map_.world_position(destination)
        duration = self.seconds_per_tile
        if continuous:
            height = linear_height(start.z, end.z, duration)
        else:
            if abs(end.z - start.z) > self.maximum_height_change:
                return None
            height = arc_height(start.z, end.z, max(start.z, end.z), duration)
        return MotionSegment(start.xy, end.xy, height, duration)
