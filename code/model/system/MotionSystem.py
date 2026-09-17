from dataclasses import replace
from math import isfinite

from pyglm import glm

class MotionSystem:
    """Advance generic motion components and clamp their height to the map."""

    @staticmethod
    def _position(segment, elapsed, map_):
        return glm.vec3(position.xy, max(position.z, map_.height(segment(elapsed))))

    def step(self, placements, motions, map_, seconds):

        placements, motions = dict(placements), dict(motions)
        for entity, motion in tuple(motions.items()):
            if entity not in placements: continue
            index = motion.segment_index
            elapsed = motion.elapsed + seconds
            position = None
            while elapsed >= motion.segments[index].duration:
                segment = motion.segments[index]
                position = self._position(segment, segment.duration, map_)
                elapsed -= segment.duration
                index += 1
                if index == len(motion.segments):
                    del motions[entity]
                    break
            else:
                segment = motion.segments[index]
                position = self._position(segment, elapsed, map_)
                motions[entity] = replace(
                    motion,
                    segment_index=index,
                    elapsed=elapsed,
                )
            placements[entity] = replace(placements[entity], position=position)
        return placements, motions
