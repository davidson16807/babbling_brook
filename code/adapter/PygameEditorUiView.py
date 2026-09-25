"""Editor status and controls, rendered through the existing UI program."""
import pygame
from pyglm import glm


class PygameEditorUiView:
    def __init__(self, program, filename, map_codec, object_palette):
        self.program = program
        self.filename = filename
        self.map_codec = map_codec
        self.object_palette = object_palette
        pygame.font.init()
        self.font = pygame.font.Font(None, 22)
        self.cache_key = None
        self.batch = None

    def draw(self, state):
        x, y = state.cursor[-1]
        red, green, blue = state.image.pixels[y*state.image.width + x]
        key = (state.viewport, tuple(state.cursor), red, green, blue, state.dirty, state.message)
        if key != self.cache_key:
            width = max(1, state.viewport[0] - 32)
            tile = self.map_codec.tile_palette[green]
            object_ = self.object_palette.get(blue, 'none')
            lines = [
                f'{self.filename} {"* unsaved" if state.dirty else "| saved"}   '
                f'Cursor ({x}, {y})   |   {len(state.cursor)} selected',
                f'Height {red*self.map_codec.height_scale:g}   |   Tile {green}: {tile}   |   Object {blue}: {object_}',
                'WASD Move   |   Shift+WASD Select rectangle   |   IJKL Rotate   |   Middle-drag Free look',
                'Wheel Height   |   Ctrl+wheel Tile   |   Shift+wheel Object   |   < > Height   [ ] Tile   9 0 Object',
                'Ctrl+S / F5 Save   |   Esc Quit' + (f'   |   {state.message}' if state.message else ''),
            ]
            wrapped = []
            for line in lines:
                current = ''
                for word in line.split():
                    candidate = (current + ' ' + word).strip()
                    if current and self.font.size(candidate)[0] > width - 24:
                        wrapped.append(current)
                        current = word
                    else:
                        current = candidate
                wrapped.append(current)
            height = 20 + len(wrapped)*24
            surface = pygame.Surface((width, height), pygame.SRCALPHA)
            surface.fill((22, 33, 37, 235))
            pygame.draw.rect(surface, (147, 169, 146), surface.get_rect(), 1)
            for i, line in enumerate(wrapped):
                color = (243, 222, 166) if i < 2 else (239, 241, 223)
                surface.blit(self.font.render(line, True, color), (12, 10 + i*24))
            self.batch = (
                'editor', surface.get_size(), pygame.image.tobytes(surface, 'RGBA', True),
                (glm.vec4(16, max(0, state.viewport[1] - height - 16), width, height),),
                (glm.vec4(0, 0, 1, 1),),
            )
            self.cache_key = key
        self.program.draw(state.viewport, *self.batch)

    def release(self):
        self.program.release()
