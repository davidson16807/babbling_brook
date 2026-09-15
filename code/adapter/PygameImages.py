from pathlib import Path
from types import SimpleNamespace
import pygame


class PygameImages:
    def __init__(self, directory: Path):
        self.directory = directory

    def read(self, name):
        surface = pygame.image.load(str(self.directory / name))
        return SimpleNamespace(size=surface.get_size(), rgba=pygame.image.tobytes(surface, 'RGBA', True))
