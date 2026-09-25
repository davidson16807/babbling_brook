"""Render terrain, PPM objects, and the editor's selected tiles."""
from collections import defaultdict

from pyglm import glm

from ..program.ViewState import ViewState


class EditorView:
    def __init__(self, tiles, objects, highlight, ui):
        self.tiles = tiles
        self.objects = objects
        self.highlight = highlight
        self.ui = ui

    def draw(self, state):
        xy = glm.vec2(*state.cursor[-1]) + glm.vec2(.5)
        target = glm.vec3(xy, state.map.height(xy))
        camera = state.camera
        aspect = state.viewport[0] / state.viewport[1]
        scale = camera.orthographic_scale / 2
        projection = glm.ortho(
            -scale * aspect,
            scale * aspect,
            -scale,
            scale,
            .1,
            100.0,
        )
        up = glm.cross(camera.right(), camera.forward())
        view = ViewState(
            projection * glm.lookAt(
                target - camera.forward() * 30,
                target,
                up,
            ),
            camera.right(),
        )
        self.tiles.draw(state.map, view)

        batches = defaultdict(lambda: ([], []))
        for placement in state.placements.values():
            definition = state.object_archetypes[placement.archetype]
            origins, sizes = batches[definition.texture]
            origins.append(placement.position)
            sizes.append(glm.vec2(definition.width, definition.height))
        for texture, (origins, sizes) in batches.items():
            self.objects.draw(
                texture,
                tuple(origins),
                tuple(sizes),
                (glm.vec4(0, 0, 1, 1),) * len(origins),
                (False,) * len(origins),
                view,
            )

        self.highlight.draw(
            state.cursor,
            tuple(state.map.corner_heights(cell) for cell in state.cursor),
            tuple(
                (1.0, .78, .12, .65 if cell == state.cursor[-1] else .35)
                for cell in state.cursor
            ),
            view,
        )
        self.ui.draw(state)

    def release(self):
        self.tiles.release()
        self.objects.release()
        self.highlight.release()
        self.ui.release()
