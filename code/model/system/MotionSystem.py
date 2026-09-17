"""Advance scripted motion without running gravity on the same entities."""
from dataclasses import replace
from math import isfinite

from pyglm import glm


class MotionSystem:
    def step(self, placements, motions, map_, seconds):
        if not isfinite(seconds) or seconds < 0:
            raise ValueError("seconds must be finite and nonnegative")
        placements, motions = dict(placements), dict(motions)
        for entity, motion in tuple(motions.items()):
            index, elapsed = motion.segment_index, motion.elapsed + seconds
            position = None
            while index < len(motion.segments):
                segment = motion.segments[index]
                position = segment(min(elapsed, segment.duration))
                if elapsed < segment.duration:
                    break
                elapsed -= segment.duration
                index += 1
            if position is not None:
                ground = map_.height(position.xy)
                if ground is None:
                    raise ValueError(f"Motion for {entity!r} leaves the map")
                placements[entity] = replace(
                    placements[entity], position=glm.vec3(position.xy, max(position.z, ground)))
            if index == len(motion.segments):
                del motions[entity]
            else:
                motions[entity] = replace(motion, segment_index=index, elapsed=elapsed)
        return placements, motions
