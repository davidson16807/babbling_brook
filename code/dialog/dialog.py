"""Standalone dialog composition root; owns imports, randomness and Pygame."""
import argparse
import os
from pathlib import Path
from random import Random
from secrets import randbits

from ..adapter.LanguagesLibrary import LanguagesLibrary
from .DialogState import DialogState


def main(argv=None):
    parser = argparse.ArgumentParser(description='Babbling Brook dialog prototype')
    parser.add_argument('--languages', type=Path, help='languages checkout or its language-learning folder')
    parser.add_argument('--seed', type=int, help='Reproduce the session inflection shuffle')
    parser.add_argument('--headless', action='store_true', help='Render offscreen with EGL')
    parser.add_argument('--frames', type=int, help='Exit after this many frames')
    parser.add_argument('--screenshot', type=Path, help='Save the last frame as PNG')
    parser.add_argument('--demo', action='store_true', help='Start with a sample sentence')
    args = parser.parse_args(argv)
    if args.frames is not None and args.frames < 1:
        parser.error('--frames must be positive')
    try:
        library = LanguagesLibrary(args.languages)
        language = library.import_module('babbling_brook.inflection.EnglishDialog')
        catalog = language.build_catalog()
    except (FileNotFoundError, ImportError) as error:
        parser.exit(1, f'Cannot load dialog language: {error}\n')
    # Third-party window state remains at the adapter/composition boundary.
    if args.headless:
        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    import moderngl
    import pygame
    from ..adapter.PygameMessageQueue import PygameMessageQueue
    from ..adapter.PygameUiView import PygameUiView
    from ..messages import WindowResizeMessage
    from ..view.program.UiProgram import UiProgram
    from .DialogUpdater import DialogUpdater
    from .DialogView import DialogView

    seed = args.seed if args.seed is not None else randbits(64)
    choices = []
    for lexeme, entry in catalog.items():
        forms = list(entry['forms'])
        Random(f'{seed}:{lexeme}').shuffle(forms)
        choices.append((lexeme, tuple(forms)))
    state = DialogState(choices=tuple(choices))
    updater = DialogUpdater(catalog, language.validate, language.sentence)
    if args.demo:
        for word in ('I', 'give', 'ball', 'boy'):
            state = updater._insert(state, word)
        state = updater._form(state, 'to the boy')
        state = updater._insert(state, 'red', ('part', 3, 1))
        state = updater._select(state, 3)
        state = updater._speak(state)

    gl = view = framebuffer = None
    try:
        pygame.display.init()
        pygame.font.init()
        if args.headless:
            gl = moderngl.create_standalone_context(require=330, backend='egl')
            framebuffer = gl.simple_framebuffer(state.viewport)
            framebuffer.use()
            queue = PygameMessageQueue(lambda: ())
        else:
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
            pygame.display.set_mode(state.viewport, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
            pygame.display.set_caption('Babbling Brook - Dialog')
            gl = moderngl.create_context(require=330)
            queue = PygameMessageQueue()
        view = DialogView(PygameUiView(UiProgram(gl)), catalog)
        clock = pygame.time.Clock()
        frames = 0
        frame_limit = args.frames or (1 if args.headless else None)
        while state.running and (frame_limit is None or frames < frame_limit):
            clock.tick(60)
            for message in queue.poll():
                if isinstance(message, WindowResizeMessage):
                    # Maintain a usable minimum canvas on small desktop windows.
                    size = max(980, message.size[0]), max(680, message.size[1])
                    if size != message.size:
                        pygame.display.set_mode(size, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
                    message = WindowResizeMessage(size)
                state = updater.update(state, message)
            gl.viewport = (0, 0, *state.viewport)
            gl.clear(0, 0, 0, 1)
            view.draw(state)
            frames += 1
            if args.screenshot and (not state.running or frames == frame_limit):
                target = framebuffer if framebuffer is not None else gl.screen
                pixels = target.read(viewport=(0, 0, *state.viewport), components=3, alignment=1)
                surface = pygame.image.frombytes(pixels, state.viewport, 'RGB', True)
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                pygame.image.save(surface, str(args.screenshot))
            if not args.headless:
                pygame.display.flip()
    finally:
        if view is not None:
            view.release()
        if framebuffer is not None:
            framebuffer.release()
        if gl is not None:
            gl.release()
        pygame.quit()


if __name__ == '__main__':
    main()
