"""Composition root: external library loading, entropy, pygame, and MVU loop."""
import argparse
import os
from pathlib import Path
import secrets


def main(argv=None):
    parser = argparse.ArgumentParser(description='Babbling Brook dialog demonstration')
    parser.add_argument('--languages', type=Path, help='Path to the external languages checkout or its language-learning folder')
    parser.add_argument('--seed', type=int, help='Reproducible dialog-session shuffle')
    parser.add_argument('--headless', action='store_true', help='Use the SDL dummy driver')
    parser.add_argument('--frames', type=int, help='Exit after this many frames')
    parser.add_argument('--screenshot', type=Path)
    parser.add_argument('--demo', choices=('walk', 'give'), help='Start with a sample constructed sentence')
    args = parser.parse_args(argv)
    if args.frames is not None and args.frames < 1:
        parser.error('--frames must be positive')
    if args.headless and args.frames is None:
        args.frames = 1
    if args.headless:
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
    import pygame
    from ..adapter.PygameMessageQueue import PygameMessageQueue
    from ..adapter.PygameDialogView import PygameDialogView
    from .DialogLanguage import DialogLanguage
    from .DialogState import DialogState
    from .DialogView import DialogView
    from .DialogGrammar import DialogGrammar
    from .DialogUpdater import DialogUpdater
    try:
        language = DialogLanguage(args.languages)
    except (OSError, ImportError, KeyError, ValueError) as error:
        parser.exit(1, f'Cannot load dialog language: {error}\n')
    state = DialogState(args.seed if args.seed is not None else secrets.randbits(128))
    view = DialogView(language)
    updater = DialogUpdater(language, view, DialogGrammar(language))
    if args.demo:
        state = updater.add(state, 'person')
        state = updater.add(state, args.demo)
        if args.demo == 'give':
            state = updater.add(state, 'ball')
            state = updater.add(state, 'red', parent=3, part_index=1)
            state = updater.add(state, 'boy')
            state = updater.choose(state, 'to the boy')
        else:
            state = updater.add(state, 'house')
            state = updater.choose(state, 'to the house')
        state = updater.talk(state)
        state = updater.open(state, 3)
    renderer = None
    try:
        pygame.display.init()
        pygame.font.init()
        surface = pygame.display.set_mode(state.viewport, pygame.RESIZABLE)
        pygame.display.set_caption('Babbling Brook - Dialog')
        renderer = PygameDialogView()
        queue = PygameMessageQueue()
        clock = pygame.time.Clock()
        frames = 0
        while state.running and (args.frames is None or frames < args.frames):
            clock.tick(60)
            for message in queue.poll():
                state = updater.update(state, message)
            if surface.get_size() != state.viewport:
                surface = pygame.display.set_mode(state.viewport, pygame.RESIZABLE)
            renderer.draw(surface, view.layout(state))
            pygame.display.flip()
            frames += 1
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(surface, str(args.screenshot))
    finally:
        if renderer:
            renderer.release()
        pygame.quit()


if __name__ == '__main__':
    main()
