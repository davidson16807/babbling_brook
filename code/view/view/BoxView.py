# HUMAN VETTED

"""Batch box materials and placements for the tile renderer."""
from collections import defaultdict
from pyglm import glm


class BoxView:
    def __init__(self, program):
        self.program = program

    def draw(self, boxes, tiles, view_state):
        batches = defaultdict(lambda: ([], [], [], []))
        for box in boxes.values():
            material = tiles[box.archetype]
            coordinates, heights, bases, scales = batches[material.top_texture, material.side_texture]
            coordinates.append(tuple(box.minimum.xy))
            heights.append(glm.mat2(*(box.position.z + 1,) * 4))
            bases.append(box.position.z)
            scales.append(box.scale)
        for (top, side), (coordinates, heights, bases, scales) in batches.items():
            self.program.draw(top, side, tuple(coordinates), tuple(heights), tuple(bases),
                              view_state, scales=tuple(scales), is_box=True)

    def release(self):
        self.program.release()
