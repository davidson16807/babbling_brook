"""Compose terrain, static level objects, cursor highlights, and editor UI."""
from collections import defaultdict

from pyglm import glm

from ..view.program.ViewState import ViewState


class EditorView:
    def __init__(self, tiles, billboards, highlights, ui, object_archetypes):
        self.tiles = tiles
        self.billboards = billboards
        self.highlights = highlights
        self.ui = ui
        self.object_archetypes = object_archetypes

    def view_state(self, state):
        camera = state.camera
        xy = glm.vec2(*state.cursor[-1]) + glm.vec2(.5)
        target = glm.vec3(xy, state.map.height(xy))
        aspect = state.viewport[0] / state.viewport[1]
        scale = camera.orthographic_scale / 2
        projection = glm.ortho(-scale*aspect, scale*aspect, -scale, scale, .1, 100.0)
        forward, right = camera.forward(), camera.right()
        # A camera-derived up vector stays valid at the allowed overhead angle.
        up = glm.cross(right, forward)
        return ViewState(projection * glm.lookAt(target - forward*30, target, up), right)

    def draw(self, state):
        view = self.view_state(state)
        self.tiles.draw(state.map, view)
        batches = defaultdict(lambda: ([], []))
        for placement in state.placements.values():
            definition = self.object_archetypes[placement.archetype]
            origins, sizes = batches[definition.texture]
            origins.append(placement.position)
            sizes.append(glm.vec2(definition.width, definition.height))
        for texture, (origins, sizes) in batches.items():
            self.billboards.draw(texture, tuple(origins), tuple(sizes),
                                 (glm.vec4(0, 0, 1, 1),) * len(origins),
                                 (False,) * len(origins), view)
        self.highlights.draw(
            state.cursor,
            tuple(state.map.corner_heights(xy) for xy in state.cursor),
            tuple((1.0, .72, .05, .55) if xy == state.cursor[-1]
                  else (.05, .65, 1.0, .35) for xy in state.cursor),
            view,
        )
        self.ui.draw(state)

    def release(self):
        self.tiles.release()
        self.billboards.release()
        self.highlights.release()
        self.ui.release()
