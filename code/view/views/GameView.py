from math import cos, sin
from pyglm import glm
from ..programs.ViewState import ViewState


class GameView:
    def __init__(self, tiles, billboards, ui):
        self.tiles, self.billboards, self.ui = tiles, billboards, ui

    def draw(self, model):
        camera = model.camera
        target = model.instances.positionables['player'] + glm.vec3(0, 0, .4)
        toward_camera = glm.vec3(cos(camera.elevation) * cos(camera.look_azimuth),
            cos(camera.elevation) * sin(camera.look_azimuth), sin(camera.elevation))
        right = glm.vec3(-sin(camera.look_azimuth), cos(camera.look_azimuth), 0)
        aspect = model.viewport[0] / model.viewport[1]
        scale = camera.orthographic_scale / 2
        projection = glm.ortho(-scale * aspect, scale * aspect, -scale, scale, .1, 100.0)
        view = ViewState(projection * glm.lookAt(target + toward_camera * 30, target, glm.vec3(0, 0, 1)), right)
        self.tiles.draw(model, view)
        self.billboards.draw(model, view)
        self.ui.draw(model)

    def release(self):
        self.tiles.release()
        self.billboards.release()
        self.ui.release()
