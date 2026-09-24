"""Edit a P3 level: python -m babbling_brook.editor path/to/level.ppm."""
import argparse
from dataclasses import replace
from pathlib import Path

# Also allow `python code/editor.py level.ppm` from a source checkout.
if not __package__:
    from importlib.util import module_from_spec, spec_from_file_location
    import sys
    spec = spec_from_file_location('babbling_brook', Path(__file__).with_name('__init__.py'),
                                  submodule_search_locations=[str(Path(__file__).parent)])
    package = module_from_spec(spec)
    sys.modules['babbling_brook'] = package
    spec.loader.exec_module(package)
    __package__ = 'babbling_brook'

import moderngl
import pygame

from .adapter.PygameEditorUiView import PygameEditorUiView
from .adapter.PygameImages import PygameImages
from .adapter.PygameMessageQueue import PygameMessageQueue
from .messages import KeyboardAction, KeyboardMessage, KeyboardModifiers
from .model.EditorFiles import EditorFiles
from .update.DirectionalKeysUpdater import DirectionalKeysUpdater
from .update.EditorUpdater import EditorUpdater
from .update.HemisphereLookUpdater import HemisphereLookUpdater
from .view.Textures import Textures
from .view.program.BillboardProgram import BillboardProgram
from .view.program.HighlightProgram import HighlightProgram
from .view.program.TileProgram import TileProgram
from .view.program.UiProgram import UiProgram
from .view.view.EditorView import EditorView
from .view.view.TileView import TileView


def main(argv=None):
    parser = argparse.ArgumentParser(description='Edit a PPM level.')
    parser.add_argument('map', type=Path, help='P3 PPM file to edit')
    args = parser.parse_args(argv)
    data = Path(__file__).resolve().parents[1] / 'data'
    files = EditorFiles(data)
    try:
        state = files.load(args.map)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'Cannot open level: {error}\n')

    context = textures = view = None
    try:
        pygame.display.init()
        pygame.font.init()
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        pygame.display.set_mode(state.viewport, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
        pygame.display.set_caption(f'Level editor — {state.filename.name}')
        context = moderngl.create_context(require=330)
        context.screen.use()
        textures = Textures(context, PygameImages(state.filename.parent / 'texture', data / 'texture'))
        names = {name for tile in state.tile_archetypes.values()
                 for name in (tile.top_texture, tile.side_texture)}
        names.update(obj.texture for obj in state.object_archetypes.values())
        for name in sorted(names):
            textures.get(name)
        view = EditorView(TileView(TileProgram(context, textures)),
                          BillboardProgram(context, textures), HighlightProgram(context),
                          PygameEditorUiView(UiProgram(context)))
        updater = EditorUpdater(DirectionalKeysUpdater(*'wasd'), DirectionalKeysUpdater(*'ijkl'),
                                HemisphereLookUpdater())
        queue = PygameMessageQueue(monitored_keys=[*'wasd', 'left ctrl', 'right ctrl'])
        clock = pygame.time.Clock()
        while state.running:
            seconds = min(clock.tick(60) / 1000, 0.25)
            messages = queue.poll()
            held = frozenset(message.key for message in messages
                             if isinstance(message, KeyboardMessage) and message.action == KeyboardAction.REPEAT)
            for message in messages:
                if isinstance(message, KeyboardMessage) and message.action == KeyboardAction.PRESS and (
                    message.key == 'f5' or message.key == 's' and message.modifiers & KeyboardModifiers.CTRL
                ):
                    try:
                        state = files.save(state)
                    except (OSError, ValueError) as error:
                        state = replace(state, message=f'Save failed: {error}')
                else:
                    state = updater.update(state, message)
            state = updater.step(state, seconds, held)
            context.viewport = (0, 0, *state.viewport)
            context.fbo.depth_mask = True
            context.clear(0.16, 0.23, 0.25, 1, depth=1)
            view.draw(state)
            pygame.display.flip()
    finally:
        if view is not None:
            view.release()
        if textures is not None:
            textures.release()
        if context is not None:
            context.release()
        pygame.quit()


if __name__ == '__main__':
    main()
