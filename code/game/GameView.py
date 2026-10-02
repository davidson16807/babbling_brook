# HUMAN VETTED

from pyglm import glm
from ..model.query.LightQuery import Light
from .. import APPLICATION_TITLE
from ..view.UiPanel import UiPanel, UiText
from ..view.program.ViewState import ViewState


class GameView:
    def __init__(self, tiles, billboards, ui, boxes=None):
        self.tiles = tiles
        self.billboards = billboards
        self.ui = ui
        self.boxes = boxes

    def ui_panels(self, game):
        def panel(title, lines, width):
            return UiPanel(
                (UiText(title, 32, 37, (243, 222, 166)),
                 *(UiText(line, 23, 26, (239, 241, 223)) for line in lines)),
                width, (22, 33, 37, 230), (147, 169, 146, 255), (16, 12, 16, 7))

        lines = ['WASD Move   Shift Run   Space Jump   E Interact',
                 'Tab Inventory   Middle-drag Rotate   F5 Save   F9 Load   Esc Quit']
        if game.message:
            lines.append(game.message)
        panels = [panel(APPLICATION_TITLE, lines, 640)]
        if game.show_inventory:
            items = [f'{item}: {quantity}'
                     for (character, item), quantity in sorted(game.inventory.items())
                     if character == 'player']
            panels.append(panel('Inventory', items or ['Your pockets are empty.'], 300))
        return tuple(panels)

    def draw(self, game, light=None):
        light = light if light is not None else Light()
        camera = game.camera
        target = game.instances.billboards['player'].position + glm.vec3(0, 0, .4)
        aspect = game.viewport[0] / game.viewport[1]
        scale = camera.orthographic_scale / 2
        projection = glm.ortho(-scale * aspect, scale * aspect, -scale, scale, .1, 100.0)
        camera_position = target - camera.forward() * 30
        view = ViewState(
            projection * glm.lookAt(camera_position, target, glm.vec3(0, 0, 1)),
            camera.right(), light.direction, light.color,
            camera_position, light.scatterers, camera.forward()
        )
        self.tiles.draw(game.map, view)
        if self.boxes is not None:
            self.boxes.draw(game.instances.boxes, game.archetypes.boxes, view)
        self.billboards.draw(
            camera,
            game.instances,
            game.archetypes,
            game.character_animation_frames,
            view,
        )
        self.ui.draw(game.viewport, self.ui_panels(game))

    def release(self):
        self.tiles.release()
        self.billboards.release()
        self.ui.release()
        if self.boxes is not None:
            self.boxes.release()
