# HUMAN VETTED

"""Advance scripted motion without running gravity on the same entities."""
from dataclasses import replace
from math import isfinite

from pyglm import glm

class MotionSystem:
    def step(self, placements, motions, motion_segments, map_, seconds):
        for entity, motion in motions.items():
            index = motion.segment_index
            elapsed = motion.elapsed + seconds
            position = None
            while index < motion.segment_count:
                segment_id = entity, index
                segment = motion_segments[segment_id]
                position = segment(min(elapsed, segment.duration))
                if elapsed < segment.duration: break
                elapsed -= segment.duration
                index += 1
            if position is not None:
                ground = map_.height(position.xy)
                placements[entity] = replace(
                    placements[entity], 
                    position=glm.vec3(position.xy, max(position.z, ground))
                )
            if index < motion.segment_count:
                motions[entity] = replace(motion, segment_index=index, elapsed=elapsed)
        return placements, motions, motion_segments
