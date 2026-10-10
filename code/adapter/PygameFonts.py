"""Pygame fonts by size, and the text metrics that layouts measure with.

Layout and rasterization must agree on text extents, so both use one instance.
The font cache is its only state, and it changes no result.
"""
import pygame


class PygameFonts:
    # The dialog mockup uses Inconsolata; fall back to common monospaced fonts.
    MONOSPACE = ('inconsolata', 'dejavusansmono', 'liberationmono', 'freemono')

    def __init__(self, path=None, names=MONOSPACE):
        pygame.font.init()
        self.path = path
        self.names = names
        self.fonts = {}

    def font(self, size: int):
        if size not in self.fonts:
            self.fonts[size] = (pygame.font.Font(str(self.path), size) if self.path
                                else pygame.font.SysFont(self.names, size))
        return self.fonts[size]

    def width(self, text: str, size: int) -> int:
        return self.font(size).size(text)[0]

    def height(self, size: int) -> int:
        return self.font(size).get_height()

    def release(self):
        self.fonts.clear()
