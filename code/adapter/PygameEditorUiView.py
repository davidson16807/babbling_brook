"""Editor controls and the selected cell's PPM values."""
import pygame
from pyglm import glm


class PygameEditorUiView:
    def __init__(self, program):
        self.program = program
        pygame.font.init()
        self.font = pygame.font.Font(None, 22)
        self.title = pygame.font.Font(None, 28)
        self.cache_key = None
        self.batch = None

    def draw(self, state):
        key = (
            state.viewport,
            tuple(state.cursor),
            id(state.image),
            state.dirty,
            state.message,
        )
        if key != self.cache_key:
            x, y = state.cursor[-1]
            height, tile, object_ = state.image.pixels[y * state.image.width + x]
            tile_name = str(state.tile_palette[tile])
            object_name = (
                'none' if object_ == 0 else str(state.object_palette[object_])
            )
            width = max(1, min(720, state.viewport[0] - 32))
            lines = [
                'WASD Cursor   Shift+WASD Select range',
                'J/L Rotate   I/K Tilt   Middle-drag Free look',
                'Wheel Height   Ctrl+Wheel Tile ID   Shift+Wheel Object ID',
                '< / > Height   [ / ] Tile ID   9 / 0 Object ID',
                'Ctrl+S / F5 Save   Ctrl+Z Undo   Ctrl+Y Redo   Esc Close',
                (
                    f'{len(state.cursor)} selected | Cell ({x}, {y})   '
                    f'Height {height * .5:g} (R {height})'
                ),
                f'Tile {tile}: {tile_name}   Object {object_}: {object_name}',
            ]
            if state.message:
                lines.append(state.message)

            wrapped = []
            for text in lines:
                line = ''
                for word in text.split():
                    candidate = (line + ' ' + word).strip()
                    if line and self.font.size(candidate)[0] > width - 24:
                        wrapped.append(line)
                        line = word
                    else:
                        line = candidate
                wrapped.append(line)

            panel = pygame.Surface(
                (width, 46 + 23 * len(wrapped)),
                pygame.SRCALPHA,
            )
            panel.fill((22, 33, 37, 230))
            pygame.draw.rect(panel, (184, 166, 100), panel.get_rect(), 1)
            title = f'Level editor | {state.filename.name}' + (' *' if state.dirty else '')
            panel.blit(
                self.title.render(title, True, (255, 220, 135)),
                (12, 10),
            )
            for row, text in enumerate(wrapped):
                panel.blit(
                    self.font.render(text, True, (239, 241, 223)),
                    (12, 42 + row * 23),
                )
            self.batch = (
                'editor-panel',
                panel.get_size(),
                pygame.image.tobytes(panel, 'RGBA', True),
                (glm.vec4(16, 16, *panel.get_size()),),
                (glm.vec4(0, 0, 1, 1),),
            )
            self.cache_key = key
        self.program.draw(state.viewport, *self.batch)

    def release(self):
        self.program.release()
