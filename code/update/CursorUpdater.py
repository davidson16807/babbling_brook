"""Move a list of selected tile coordinates without terrain or object collision."""
from math import floor, pi

from pyglm import glm


class CursorUpdater:
    def __init__(self, vector_updater):
        self.vector_updater = vector_updater

    def translate(self, cursor, dimensions, offset):
        """Move a selected group together, keeping its shape inside the map."""
        dx = max(-min(x for x, _ in cursor),
                 min(dimensions.x - 1 - max(x for x, _ in cursor), int(offset.x)))
        dy = max(-min(y for _, y in cursor),
                 min(dimensions.y - 1 - max(y for _, y in cursor), int(offset.y)))
        return [(x + dx, y + dy) for x, y in cursor]

    def update(self, cursor, dimensions, camera, messages, extend=False):
        axes = glm.vec2(0)
        for message in messages:
            axes = self.vector_updater.update(axes, message)
        if not axes.x and not axes.y:
            return cursor
        # Choose the closest cardinal basis to the camera. WASD can reach every
        # tile even when the displayed camera is diagonal or directly overhead.
        quadrant = floor(camera.look_azimuth / (pi / 2) + .5) % 4
        forward = ((-1, 0), (0, -1), (1, 0), (0, 1))[quadrant]
        right = (forward[1], -forward[0])
        x, y = cursor[-1]
        head = (
            max(0, min(dimensions.x - 1, x + int(right[0]*axes.x + forward[0]*axes.y))),
            max(0, min(dimensions.y - 1, y + int(right[1]*axes.x + forward[1]*axes.y))),
        )
        if not extend:
            return [head]
        anchor = cursor[0]
        if head == anchor:
            return [head]
        # Keep the endpoints in the list itself; no separate single-tile cursor.
        middle = [
            (x, y)
            for y in range(min(anchor[1], head[1]), max(anchor[1], head[1]) + 1)
            for x in range(min(anchor[0], head[0]), max(anchor[0], head[0]) + 1)
            if (x, y) not in (anchor, head)
        ]
        return [anchor, *middle, head]
