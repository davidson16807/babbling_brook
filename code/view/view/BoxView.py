# HUMAN VETTED

"""Batch box archetypes and placements for the tile renderer."""
from collections import defaultdict
from pyglm import glm


class BoxView:
    def __init__(self, program):
        self.program = program

    def draw(self, boxes, archetypes, view_state):
        batches = defaultdict(lambda: ([], [], []))
        for box in boxes.values():
            archetype = archetypes[box.archetype]
            coordinates, heights, bases = batches[box.archetype]
            coordinates.append(tuple(archetype.bounds(box.position).minimum.xy))
            heights.append(glm.mat2(*(box.position.z + 1,) * 4))
            bases.append(box.position.z)
        for key, (coordinates, heights, bases) in batches.items():
            archetype = archetypes[key]
            self.program.draw(archetype.top_texture, archetype.side_texture,
                              tuple(coordinates), tuple(heights), tuple(bases),
                              view_state, scale=archetype.scale, is_box=True,
                              cull_back_faces=True)

    def release(self):
        self.program.release()
