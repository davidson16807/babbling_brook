"""Dialog mode: compose statements in the dialog GUI, without the world.

Run from the repository root with:

    python demo/dialog/main.py
    python demo/dialog/main.py --demo --seed 7      # start with "you give the red ball to the boy"
    python demo/dialog/main.py --headless --demo --frames 2 --screenshot dialog.png

It needs the languages repo at lib/languages (or ../languages, --languages PATH, or
$BB_LANGUAGES). Pygame window, input, and timing stay here; `DialogState`,
`DialogUpdater`, and `DialogView` form the MVU loop. Trainer mode is meant to nest
the same three.
"""
import argparse
import sys
import time
from dataclasses import replace
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import moderngl
import pygame

ROOT = Path(__file__).resolve().parents[2]

# Make the source checkout runnable before an editable install. The demo remains
# outside the babbling_brook package and is not included in its package list.
if 'babbling_brook' not in sys.modules:
    spec = spec_from_file_location(
        'babbling_brook',
        ROOT / 'code' / '__init__.py',
        submodule_search_locations=[str(ROOT / 'code')],
    )
    package = module_from_spec(spec)
    sys.modules['babbling_brook'] = package
    spec.loader.exec_module(package)

from babbling_brook import APPLICATION_TITLE
from babbling_brook.adapter.PygameFonts import PygameFonts
from babbling_brook.adapter.PygameMessageQueue import PygameMessageQueue
from babbling_brook.adapter.PygameUiBoxView import PygameUiBoxView
from babbling_brook.adapter.LanguagesLibrary import LanguagesLibrary
from babbling_brook.messages import QuitMessage
from babbling_brook.view.program.UiProgram import UiProgram
from babbling_brook.dialog.DialogLayout import DialogLayout, DialogMetrics
from babbling_brook.dialog.DialogState import DialogState
from babbling_brook.dialog.DialogUpdater import DialogUpdater
from babbling_brook.dialog.DialogView import DialogView, dialog_styles
from babbling_brook.dialog.RuleAddresses import RuleAddresses

from DialogDemo import DialogDemo  # beside this script, which Python puts on sys.path

BACKGROUND = (.29, .38, .64)


def main(argv=None):
    parser = argparse.ArgumentParser(description=f'{APPLICATION_TITLE} dialog harness')
    parser.add_argument('--languages', type=Path,
                        help='The languages repo (default: lib/languages, then ../languages)')
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
        library = LanguagesLibrary(args.languages)
    except FileNotFoundError as error:
        parser.exit(1, f'{error}\n')
    print(f'Building English with {library.directory}…', flush=True)
    english = library.import_module('babbling_brook.inflection.english')

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
            pygame.display.set_caption(f'{APPLICATION_TITLE} - Dialog (English)')
            gl = moderngl.create_context(require=330)
            gl.screen.use()
            queue = PygameMessageQueue()
        fonts = PygameFonts(args.font)
        addresses = RuleAddresses()
        layout = DialogLayout(english.inventory(), DialogMetrics(fonts, args.font_size),
                              addresses=addresses, text=english.text)
        updater = DialogUpdater(layout, addresses=addresses, text=english.text, lexeme=english.lexeme,
                                inflections=english.inflections, default_inflection=english.default_inflection)
        view = DialogView(layout, PygameUiBoxView(UiProgram(gl), fonts), dialog_styles(args.font_size))
        seed = args.seed if args.seed is not None else time.time_ns()
        state = DialogState(english.clause(), viewport=viewport, seed=seed)
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
                if outcome is not None:
                    if outcome.content:
                        said = english.text(outcome)
                        print(said, flush=True)
                        state = replace(state, message=f'You said: "{said}"')
                    else:
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
