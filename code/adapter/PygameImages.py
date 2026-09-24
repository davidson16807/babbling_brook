from pathlib import Path
from types import SimpleNamespace
import pygame


class PygameImages:
    def __init__(self, directory: Path, fallback_directory: Path | None = None):
        self.directory = directory
        self.fallback_directory = fallback_directory

    def read(self, name):
        path = self.directory / name
        if not path.is_file() and self.fallback_directory is not None:
            path = self.fallback_directory / name
        surface = pygame.image.load(str(path))
        return SimpleNamespace(size=surface.get_size(), rgba=pygame.image.tobytes(surface, 'RGBA', True))
