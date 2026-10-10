"""Dialog harness composition root: compose statements without the world.

Pygame window, input, and timing stay here; `DialogState`, `DialogUpdater`, and
`DialogView` form the MVU loop. Trainer mode is meant to nest the same three.
"""
import argparse
import time
from dataclasses import replace
from pathlib import Path

import moderngl
import pygame

from .. import APPLICATION_TITLE
from ..adapter.PygameFonts import PygameFonts
from ..adapter.PygameMessageQueue import PygameMessageQueue
from ..adapter.PygameUiBoxView import PygameUiBoxView
from ..codec.LexiconCodec import LexiconStringCodec
from ..messages import QuitMessage
from ..view.program.UiProgram import UiProgram
from .DialogDemo import DialogDemo
from .DialogLayout import DialogLayout, DialogMetrics
from .DialogState import DialogState, Dismissed, Spoke
from .DialogUpdater import DialogUpdater
from .DialogView import DialogView, dialog_styles
from .playmat import describe, tokens

ROOT = Path(__file__).resolve().parents[2]
BACKGROUND = (.29, .38, .64)


def main(argv=None):
    parser = argparse.ArgumentParser(description=f'{APPLICATION_TITLE} dialog harness')
    parser.add_argument('--lexicon', type=Path, default=ROOT / 'data' / 'lexicon' / 'english.tsv')
    parser.add_argument('--font', type=Path, help='TTF/OTF file; defaults to a monospaced system font')
    parser.add_argument('--font-size', type=int, default=22)
    parser.add_argument('--seed', type=int, help='Inflection grid order (default: new each run)')
    parser.add_argument('--size', default='1280x720', help='Window size, WIDTHxHEIGHT')
    parser.add_argument('--demo', action='store_true', help='Start with the mockup statement composed')
    parser.add_argument('--frames', type=int, help='Exit after this many frames (smoke testing)')
    parser.add_argument('--headless', action='store_true', help='Render offscreen with EGL')
    parser.add_argument('--screenshot', type=Path, help='Write the final frame to a PNG')
    args = parser.parse_args(argv)
    viewport = tuple(int(n) for n in args.size.lower().split('x'))
    if args.headless and args.frames is None:
        args.frames = 1
    try:
        lexicon = LexiconStringCodec().decode(args.lexicon.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        parser.exit(1, f'Cannot read lexicon: {error}\n')

    gl = view = framebuffer = fonts = None
    try:
        if args.headless:
            gl = moderngl.create_standalone_context(require=330, backend='egl')
            framebuffer = gl.simple_framebuffer(viewport)
            framebuffer.use()
            queue = PygameMessageQueue(lambda: ())
        else:
            pygame.display.init()
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
            pygame.display.set_mode(viewport, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
            pygame.display.set_caption(f'{APPLICATION_TITLE} - Dialog ({lexicon.language})')
            gl = moderngl.create_context(require=330)
            gl.screen.use()
            queue = PygameMessageQueue()
        fonts = PygameFonts(args.font)
        layout = DialogLayout(lexicon, DialogMetrics(fonts, args.font_size))
        updater = DialogUpdater(layout)
        view = DialogView(layout, PygameUiBoxView(UiProgram(gl), fonts), dialog_styles(args.font_size))
        seed = args.seed if args.seed is not None else time.time_ns()
        state = DialogState(viewport=viewport, seed=seed)
        if args.demo:
            state = DialogDemo(updater).mockup(state)
        clock = pygame.time.Clock()
        running, frames = True, 0
        while running and (args.frames is None or frames < args.frames):
            if not args.headless:
                clock.tick(60)
            for message in queue.poll():
                if isinstance(message, QuitMessage):
                    running = False
                    break
                state, outcome = updater.update(state, message)
                if isinstance(outcome, Spoke):
                    print(describe(outcome.playmat, lexicon), flush=True)
                    state = replace(state, message=f'You said: "{" ".join(tokens(outcome.playmat, lexicon))}"')
                elif isinstance(outcome, Dismissed):
                    state = replace(state, message='Dismissed. Trainer mode would close the dialog here.')
            gl.viewport = (0, 0, *state.viewport)
            gl.clear(*BACKGROUND, 1.0)
            view.draw(state)
            frames += 1
            if args.screenshot and (not running or args.frames is not None and frames >= args.frames):
                target = framebuffer if framebuffer is not None else gl.screen
                pixels = target.read(viewport=(0, 0, *state.viewport), components=3, alignment=1)
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                pygame.image.save(pygame.image.frombytes(pixels, state.viewport, 'RGB', True),
                                  str(args.screenshot))
            if not args.headless:
                pygame.display.flip()
    finally:
        if view is not None:
            view.release()
        if fonts is not None:
            fonts.release()
        if framebuffer is not None:
            framebuffer.release()
        if gl is not None:
            gl.release()
        pygame.quit()


if __name__ == '__main__':
    main()
