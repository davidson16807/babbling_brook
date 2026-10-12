"""Dialog composition root: Pygame window and a strict Model/View/Update loop."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from .DialogLexicon import english_lexicon
from .DialogMessages import Resize
from .DialogState import DialogState
from .DialogUpdater import DialogUpdater
from .DialogView import DialogView


def main(argv=None):
    parser = argparse.ArgumentParser(description='Babbling Brook dialog mode')
    parser.add_argument('--seed', type=int, default=16807,
                        help='Session seed for per-lexeme inflection order')
    parser.add_argument('--frames', type=int,
                        help='Exit after this many frames (smoke testing)')
    parser.add_argument('--headless', action='store_true',
                        help='Use SDL dummy video (implies one frame unless --frames is set)')
    parser.add_argument('--screenshot', type=Path, help='Save the final frame as PNG')
    args = parser.parse_args(argv)
    if args.frames is not None and args.frames <= 0:
        parser.error('--frames must be positive')
    if args.headless:
        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        if args.frames is None:
            args.frames = 1

    try:
        import pygame
    except ImportError as error:
        parser.error('dialog mode requires pygame-ce; install with: python -m pip install -e ".[render]"')
        raise error  # pragma: no cover
    from .PygameDialogAdapter import PygameDialogAdapter

    pygame.init()
    model = DialogState(english_lexicon(), session_seed=args.seed)
    flags = pygame.RESIZABLE
    screen = pygame.display.set_mode(model.viewport, flags)
    pygame.display.set_caption('Babbling Brook - Dialog')
    adapter = PygameDialogAdapter(pygame, screen)
    updater, view = DialogUpdater(), DialogView()
    clock, frames = pygame.time.Clock(), 0
    try:
        while model.running and (args.frames is None or frames < args.frames):
            for message in adapter.messages():
                model = updater.update(model, message)
            if screen.get_size() != model.viewport:
                model = updater.update(model, Resize(screen.get_size()))
            adapter.draw(view.scene(model))
            pygame.display.flip()
            frames += 1
            clock.tick(60)
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(screen, str(args.screenshot))
    finally:
        adapter.release()
        pygame.quit()


if __name__ == '__main__':
    main()
