"""Compose terrain, static level objects, cursor highlights, and editor UI."""
from collections import defaultdict

from pyglm import glm
from ..model.query.LightQuery import Light

from ..view.program.ViewState import ViewState
from ..view.UiPanel import UiPanel, UiText


class EditorView:
    def __init__(self, tiles, billboards, highlights, ui, billboard_archetypes,
                 filename, map_codec, object_palette, boxes=None):
        self.tiles = tiles
        self.billboards = billboards
        self.highlights = highlights
        self.ui = ui
        self.billboard_archetypes = billboard_archetypes
        self.filename = filename
        self.map_codec = map_codec
        self.object_palette = object_palette
        self.boxes = boxes

    def ui_panels(self, state):
        x, y = state.cursor[-1]
        red, green, blue = state.content.image.pixels[y*state.content.image.width + x]
        tile = self.map_codec.tile_palette.get(green, 'missing')
        object_ = self.object_palette.get(blue, 'none' if blue == 0 else 'missing')
        mode = 'Zoom' if state.channel is None else ('Height [0]', 'Tile [1]', 'Object [2]')[state.channel]
        if state.time_mode:
            mode = 'Time'
        elif state.object_step is not None:
            mode = f'Move {len(state.selected_objects)} objects ({state.object_step:g} units)'
        clipboard = (f'{state.clipboard.width} x {state.clipboard.height}'
                     if state.clipboard is not None else 'empty')
        lines = (
            f'{self.filename} {"* unsaved" if state.dirty else "| saved"}   '
            f'Cursor ({x}, {y})   |   {len(state.cursor)} selected',
            f'Height {red*self.map_codec.height_scale:g}   |   Tile {green}: {tile}   |   Object {blue}: {object_}',
            f'Mode: {mode}   |   Zoom span {state.camera.orthographic_scale:g}   |   '
            f'Clipboard: {clipboard}   |   Undo {len(state.undo_history)} / Redo {len(state.redo_history)}',
            'WASD Move   |   Shift+WASD Select rectangle   |   IJKL Rotate   |   Middle-drag Free look',
            'Wheel / < > Adjust mode   |   + - Zoom   |   R Height   G Tile   B Object   Esc Zoom',
            f'T Time mode   |   < > / wheel Reverse / forward   |   0 or / Pause   |   {state.time_warp:g}x',
            'E Move objects (1)   |   Ctrl+E Fine move (0.1)   |   WASD XY   Q Up / Z Down   |   Esc Snap fine move',
            '0-9 Set channel   |   / or Delete Zero   |   Ctrl+C Copy   Ctrl+V Paste',
            'Ctrl+Z Undo   |   Ctrl+Shift+Z / Ctrl+Y Redo   |   Ctrl+S / F5 Save   |   Close window Quit',
            state.message or 'Ready.',
        )
        return (UiPanel(
            tuple(UiText(line, 22, 24, (243, 222, 166) if i < 2 else (239, 241, 223))
                  for i, line in enumerate(lines)),
            None, (22, 33, 37, 235), (147, 169, 146, 255), (12, 10, 12, 10),
            anchor='bottom-left'),)

    def view_state(self, state, light=None):
        light = light if light is not None else Light()
        camera = state.camera
        xy = glm.vec2(*state.cursor[-1]) + glm.vec2(.5)
        target = glm.vec3(xy, state.map.height(xy))
        aspect = state.viewport[0] / state.viewport[1]
        scale = camera.orthographic_scale / 2
        projection = glm.ortho(-scale*aspect, scale*aspect, -scale, scale, .1, 100.0)
        forward, right = camera.forward(), camera.right()
        # A camera-derived up vector stays valid at the allowed overhead angle.
        up = glm.cross(right, forward)
        return ViewState(projection * glm.lookAt(target - forward*30, target, up), right,
                         light.direction, light.color)

    def draw(self, state, light=None):
        view = self.view_state(state, light)
        self.tiles.draw(state.map, view)
        if self.boxes is not None:
            self.boxes.draw(state.content.boxes, self.map_codec.tile_archetypes, view)
        batches = defaultdict(lambda: ([], []))
        for placement in (*state.content.billboards.values(), *state.content.character_instances.values()):
            definition = self.billboard_archetypes[placement.archetype]
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
        self.ui.draw(state.viewport, self.ui_panels(state))

    def release(self):
        self.tiles.release()
        self.billboards.release()
        self.highlights.release()
        self.ui.release()
        if self.boxes is not None:
            self.boxes.release()
