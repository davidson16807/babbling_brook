"""Desktop level-editor composition root."""
import argparse
from dataclasses import replace
from math import pi
from pathlib import Path

import moderngl
import pygame

from . import APPLICATION_TITLE
from .adapter.PygameEditorUiView import PygameEditorUiView
from .adapter.PygameImages import PygameImages
from .adapter.PygameMessageQueue import PygameMessageQueue
from .messages import KeyboardAction, KeyboardMessage, KeyboardModifiers
from .model.EditorFiles import EditorFiles
from .update.DirectionalKeysUpdater import DirectionalKeysUpdater
from .update.EditorUpdater import EditorUpdater
from .update.LookUpdater import VectorKeysUpdater, VectorMouseUpdater
from .view.Textures import Textures
from .view.program.BillboardProgram import BillboardProgram
from .view.program.HighlightProgram import HighlightProgram
from .view.program.TileProgram import TileProgram
from .view.program.UiProgram import UiProgram
from .view.view.EditorView import EditorView
from .view.view.TileView import TileView


def main(argv=None):
    parser = argparse.ArgumentParser(description=f'{APPLICATION_TITLE} level editor')
    parser.add_argument('map', type=Path, help='P3 PPM level file to edit')
    args = parser.parse_args(argv)
    if args.map.suffix.lower() != '.ppm':
        parser.error('the level filename must end in .ppm')

    files = EditorFiles(Path('data'))
    try:
        state = files.load(args.map)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Cannot load level: {error}\n')

    pygame.display.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(
        pygame.GL_CONTEXT_PROFILE_MASK,
        pygame.GL_CONTEXT_PROFILE_CORE,
    )
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
    pygame.display.set_mode(
        state.viewport,
        pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE,
    )
    pygame.display.set_caption(f'{APPLICATION_TITLE} level editor — {state.filename.name}')

    context = moderngl.create_context(require=330)
    context.screen.use()
    texture_directory = state.filename.parent / 'texture'
    if not texture_directory.is_dir():
        texture_directory = Path('data') / 'texture'
    textures = Textures(context, PygameImages(texture_directory))
    view = None
    try:
        names = {
            texture
            for item in state.tile_archetypes.values()
            for texture in (item.top_texture, item.side_texture)
        } | {item.texture for item in state.object_archetypes.values()}
        for name in sorted(names):
            textures.get(name)

        view = EditorView(
            TileView(TileProgram(context, textures)),
            BillboardProgram(context, textures),
            HighlightProgram(context),
            PygameEditorUiView(UiProgram(context)),
        )
        updater = EditorUpdater(
            DirectionalKeysUpdater(*'wasd'),
            VectorKeysUpdater(*'ijkl', magnitude=(pi/2, pi/6)),
            VectorMouseUpdater(-.01),
        )
        queue = PygameMessageQueue(monitored_keys=[
            *'wasd',
            'shift',
            'right shift',
            'left ctrl',
            'right ctrl',
        ])
        clock = pygame.time.Clock()

        while state.running:
            seconds = min(clock.tick(60) / 1000.0, .25)
            messages = queue.poll()
            pressed_keys = frozenset(
                message.key
                for message in messages
                if (
                    isinstance(message, KeyboardMessage)
                    and message.action == KeyboardAction.REPEAT
                )
            )
            for message in messages:
                save = (
                    isinstance(message, KeyboardMessage)
                    and message.action == KeyboardAction.PRESS
                    and (
                        message.key == 'f5'
                        or message.key == 's'
                        and message.modifiers & KeyboardModifiers.CTRL
                    )
                )
                if save:
                    try:
                        state = files.save(state)
                    except (OSError, ValueError) as error:
                        state = replace(state, message=f'Save failed: {error}')
                else:
                    state = updater.update(state, message)
            state = updater.step(state, seconds, pressed_keys)

            context.viewport = (0, 0, *state.viewport)
            context.fbo.depth_mask = True
            context.clear(.11, .16, .18, 1, depth=1)
            view.draw(state)
            pygame.display.flip()
    finally:
        if view is not None:
            view.release()
        textures.release()
        context.release()
        pygame.quit()


if __name__ == '__main__':
    main()
