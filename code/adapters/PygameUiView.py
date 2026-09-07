import pygame
from pyglm import glm


class PygameUiView:
    def __init__(self, program):
        self.program = program
        pygame.font.init()
        self.font = pygame.font.Font(None, 23)
        self.title = pygame.font.Font(None, 32)
        self.cache_key = None
        self.panels = None

    def _panel(self, width, lines, title):
        surface = pygame.Surface((width, 56 + 26 * len(lines)), pygame.SRCALPHA)
        surface.fill((22, 33, 37, 230))
        pygame.draw.rect(surface, (147, 169, 146, 255), surface.get_rect(), 1)
        surface.blit(self.title.render(title, True, (243, 222, 166)), (16, 12))
        for index, text in enumerate(lines):
            surface.blit(self.font.render(text, True, (239, 241, 223)), (16, 49 + index * 26))
        return surface

    def draw(self, model):
        key = (model.viewport, model.message, model.show_inventory, tuple(sorted(model.inventory.items())))
        if key != self.cache_key:
            width = min(640, max(240, model.viewport[0] - 32))
            lines = ['WASD Move   Shift Run   Space Jump   E Interact',
                     'Tab Inventory   Middle-drag Rotate   F5 Save   F9 Load   Esc Quit']
            if model.message:
                # Wrap by rendered width so error/status text remains visible.
                line = ''
                for word in model.message.split():
                    if self.font.size((line + ' ' + word).strip())[0] > width - 32 and line:
                        lines.append(line)
                        line = word
                    else:
                        line = (line + ' ' + word).strip()
                if line:
                    lines.append(line)
            panels = [('help', 16, 16, self._panel(width, lines, 'Babbling Brook'))]
            if model.show_inventory:
                items = [f'{item}: {quantity}' for item, quantity in sorted(model.inventory.items())] or ['Your pockets are empty.']
                panels.append(('inventory', 16, panels[0][3].get_height() + 28,
                    self._panel(min(300, width), items, 'Inventory')))
            self.panels = tuple((name, glm.vec4(x, y, *surface.get_size()), surface.get_size(), pygame.image.tobytes(surface, 'RGBA', True))
                for name, x, y, surface in panels)
            self.cache_key = key
        self.program.draw(model.viewport, *(tuple(panel[i] for panel in self.panels) for i in range(4)))

    def release(self):
        self.program.release()
