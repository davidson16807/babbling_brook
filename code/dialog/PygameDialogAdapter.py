"""The complete Pygame boundary: event translation and scene rasterization."""
from __future__ import annotations

from .DialogMessages import KeyPress, PointerDown, PointerMove, PointerUp, Quit, Resize


class PygameDialogAdapter:
    def __init__(self, pygame, screen):
        self.pygame = pygame
        self.screen = screen
        self.fonts = {}

    def font(self, size):
        if size not in self.fonts:
            self.fonts[size] = self.pygame.font.SysFont(
                ('inconsolata', 'dejavusansmono', 'liberationmono', 'freemono'), size)
        return self.fonts[size]

    def messages(self):
        result = []
        pg = self.pygame
        for event in pg.event.get():
            if event.type == pg.QUIT:
                result.append(Quit())
            elif event.type == pg.KEYDOWN and not getattr(event, 'repeat', False):
                result.append(KeyPress(pg.key.name(event.key)))
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                result.append(PointerDown(tuple(event.pos)))
            elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
                result.append(PointerUp(tuple(event.pos)))
            elif event.type == pg.MOUSEMOTION:
                result.append(PointerMove(tuple(event.pos)))
            elif event.type in (pg.WINDOWRESIZED, pg.WINDOWSIZECHANGED):
                result.append(Resize((event.x, event.y)))
        return tuple(result)

    def draw(self, scene):
        pg, surface = self.pygame, self.screen
        surface.fill((244, 241, 228))
        # A tiny decorative scene keeps this mode visually related to the
        # text-adventure mockup without depending on the 3D game world.
        for x, y, shirt in ((scene.viewport[0] - 160, 150, (117, 170, 112)),
                            (scene.viewport[0] - 320, 220, (114, 168, 184))):
            pg.draw.circle(surface, (221, 181, 133), (x, y), 18)
            pg.draw.rect(surface, shirt, (x - 20, y + 16, 40, 48))
            pg.draw.rect(surface, (78, 62, 48), (x - 18, y - 23, 36, 10))
        for box in scene.boxes:
            rect = pg.Rect(box.rect)
            pg.draw.rect(surface, box.fill, rect, border_radius=box.radius)
            if box.border_width:
                pg.draw.rect(surface, box.border, rect, box.border_width,
                             border_radius=box.radius)
            if box.text:
                rendered = self.font(box.font_size).render(box.text, True, box.text_color)
                surface.blit(rendered, rendered.get_rect(center=rect.center))
        for label in scene.texts:
            surface.blit(self.font(label.font_size).render(label.text, True, label.color),
                         label.position)

    def release(self):
        self.fonts.clear()
