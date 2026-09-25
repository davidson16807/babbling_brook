# HUMAN VETTED

from pyglm import glm
from ..view.program.ViewState import ViewState


class GameView:
    def __init__(self, tiles, billboards, ui):
        self.tiles = tiles
        self.billboards = billboards
        self.ui = ui

    def draw(self, game):
        camera = game.camera
        target = game.instances.placements['player'].position + glm.vec3(0, 0, .4)
        aspect = game.viewport[0] / game.viewport[1]
        scale = camera.orthographic_scale / 2
        projection = glm.ortho(-scale * aspect, scale * aspect, -scale, scale, .1, 100.0)
        view = ViewState(
            projection * glm.lookAt(target + -camera.forward() * 30, target, glm.vec3(0, 0, 1)), 
            camera.right()
        )
        self.tiles.draw(game.map, view)
        self.billboards.draw(
            camera,
            game.instances,
            game.archetypes,
            game.character_animation_frames,
            view,
        )
        self.ui.draw(game)

    def release(self):
        self.tiles.release()
        self.billboards.release()
        self.ui.release()
