"""Rasterize plain text panels with Pygame and submit a single UI atlas."""
import pygame
from pyglm import glm

from ..view.UiPanel import UiPanel


class PygameUiView:
    def __init__(self, program):
        self.program = program
        pygame.font.init()
        self.fonts = {}
        self.cache_key = None
        self.batch = None

    def _font(self, size):
        if size not in self.fonts:
            self.fonts[size] = pygame.font.Font(None, size)
        return self.fonts[size]

    def _wrap(self, text, font, width):
        for paragraph in text.split('\n'):
            line = ''
            for word in paragraph.split():
                candidate = f'{line} {word}' if line else word
                if line and font.size(candidate)[0] > width:
                    yield line
                    line = ''
                # Split long words too, so paths and identifiers remain readable.
                if not line:
                    chunk = ''
                    for character in word:
                        if chunk and font.size(chunk + character)[0] > width:
                            yield chunk
                            chunk = ''
                        chunk += character
                    line = chunk
                else:
                    line = candidate
            yield line

    def _panel(self, panel, viewport):
        available = max(1, viewport[0] - 2 * panel.margin[0])
        width = available if panel.width is None else max(1, min(panel.width, available))
        left, top, right, bottom = panel.padding
        wrapped = [(line, style) for style in panel.lines
                   for line in self._wrap(style.text, self._font(style.font_size),
                                          max(1, width - left - right))]
        height = max(1, top + bottom + sum(style.line_height for _, style in wrapped))
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill(panel.background)
        pygame.draw.rect(surface, panel.border, surface.get_rect(), 1)
        y = top
        for line, style in wrapped:
            surface.blit(self._font(style.font_size).render(line, True, style.color), (left, y))
            y += style.line_height
        return surface

    def draw(self, viewport: tuple[int, int], panels: tuple[UiPanel, ...]):
        key = (tuple(viewport), tuple(panels))
        if key != self.cache_key:
            surfaces = [self._panel(panel, viewport) for panel in panels]
            self.batch = None
            if surfaces:
                atlas_width = max(surface.get_width() for surface in surfaces)
                atlas_height = sum(surface.get_height() for surface in surfaces)
                atlas = pygame.Surface((atlas_width, atlas_height), pygame.SRCALPHA)
                atlas.fill((0, 0, 0, 0))
                rects, uv_rects = [], []
                offsets = {'top-left': 0, 'bottom-left': 0}
                atlas_y = 0
                for panel, surface in zip(panels, surfaces):
                    width, height = surface.get_size()
                    offset = panel.margin[1] + offsets[panel.anchor]
                    y = offset if panel.anchor == 'top-left' else max(0, viewport[1] - offset - height)
                    rects.append(glm.vec4(panel.margin[0], y, width, height))
                    offsets[panel.anchor] += height + panel.gap
                    atlas.blit(surface, (0, atlas_y))
                    # Inset UVs to avoid sampling a neighbouring panel's border.
                    uv_rects.append(glm.vec4(
                        .5 / atlas_width,
                        1 - (atlas_y + height - .5) / atlas_height,
                        (width - .5) / atlas_width,
                        1 - (atlas_y + .5) / atlas_height,
                    ))
                    atlas_y += height
                self.batch = ('panels', atlas.get_size(),
                              pygame.image.tobytes(atlas, 'RGBA', True),
                              tuple(rects), tuple(uv_rects))
            self.cache_key = key
        if self.batch is not None:
            self.program.draw(viewport, *self.batch)

    def release(self):
        self.fonts.clear()
        self.program.release()
