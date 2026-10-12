"""Rasterize `UiBox`es with Pygame and draw them in one `UiProgram` call.

Boxes with text are rasterized once per distinct (size, style, text) and kept
while they stay on screen. Plain boxes and borders are stretched from small
color swatches. Moving a box therefore changes only its rect: a dragged chip
is not rasterized again. Caches are pure functions of their keys; clearing
them changes nothing but speed.
"""
from dataclasses import dataclass

import pygame
from pyglm import glm

from ..view.UiBox import UiBox


@dataclass(frozen=True)
class _Atlas:
    size: tuple[int, int]
    rgba: bytes
    uv_rects: dict  # key -> glm.vec4


class PygameUiBoxView:
    SWATCH = 3  # swatch side; sampling its center pixel avoids bleeding from neighbors

    def __init__(self, program, fonts, atlas_width=1024):
        self.program = program
        self.fonts = fonts
        self.atlas_width = atlas_width
        self.atlas = None

    def _text(self, key):
        _, width, height, style, text = key
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill(style.background)
        if style.border_width:
            pygame.draw.rect(surface, style.border, surface.get_rect(), style.border_width)
        rendered = self.fonts.font(style.font_size).render(text, True, style.text_color)
        surface.blit(rendered, ((width - rendered.get_width()) // 2,
                                (height - rendered.get_height()) // 2))
        return surface

    def _swatch(self, key):
        surface = pygame.Surface((self.SWATCH, self.SWATCH), pygame.SRCALPHA)
        surface.fill(key[1])
        return surface

    def _pack(self, keys):
        """Shelf-pack one surface per key into a fresh atlas."""
        surfaces = {key: self._text(key) if key[0] == 'text' else self._swatch(key) for key in keys}
        order = sorted(surfaces, key=lambda key: -surfaces[key].get_height())
        width = max([self.atlas_width, *(surface.get_width() for surface in surfaces.values())])
        positions, x, y, shelf = {}, 0, 0, 0
        for key in order:
            w, h = surfaces[key].get_size()
            if x + w > width:
                x, y, shelf = 0, y + shelf, 0
            positions[key] = (x, y)
            x, shelf = x + w, max(shelf, h)
        height = max(1, y + shelf)
        atlas = pygame.Surface((width, height), pygame.SRCALPHA)
        atlas.fill((0, 0, 0, 0))
        uv_rects = {}
        for key, (x, y) in positions.items():
            w, h = surfaces[key].get_size()
            atlas.blit(surfaces[key], (x, y))
            if key[0] == 'text':
                # Inset half a texel, as PygameUiView does, so pixels map one to one.
                uv_rects[key] = glm.vec4((x + .5) / width, 1 - (y + h - .5) / height,
                                         (x + w - .5) / width, 1 - (y + .5) / height)
            else:
                u, v = (x + w / 2) / width, 1 - (y + h / 2) / height
                uv_rects[key] = glm.vec4(u, v, u, v)
        return _Atlas((width, height), pygame.image.tobytes(atlas, 'RGBA', True), uv_rects)

    def quads(self, boxes):
        """(atlas key, rect) pairs in draw order."""
        quads = []
        for box in boxes:
            x, y, w, h = (round(value) for value in box.rect)
            if w <= 0 or h <= 0:
                continue
            style = box.style
            if box.text:
                quads.append((('text', w, h, style, box.text), (x, y, w, h)))
                continue
            b = min(style.border_width, w // 2, h // 2)
            if style.background[3]:
                quads.append((('color', style.background), (x + b, y + b, w - 2 * b, h - 2 * b)))
            if b and style.border[3]:
                border = ('color', style.border)
                quads += [(border, (x, y, w, b)), (border, (x, y + h - b, w, b)),
                          (border, (x, y + b, b, h - 2 * b)), (border, (x + w - b, y + b, b, h - 2 * b))]
        return quads

    def draw(self, viewport: tuple[int, int], boxes: tuple[UiBox, ...]):
        quads = self.quads(boxes)
        if not quads:
            return
        keys = {key for key, _ in quads}
        if self.atlas is None or not keys <= self.atlas.uv_rects.keys():
            # Repack with only what is on screen now, so the atlas never grows without bound.
            self.atlas = self._pack(keys)
        self.program.draw(viewport, 'ui-boxes', self.atlas.size, self.atlas.rgba,
                          tuple(glm.vec4(*rect) for _, rect in quads),
                          tuple(self.atlas.uv_rects[key] for key, _ in quads))

    def release(self):
        self.atlas = None
        self.program.release()
