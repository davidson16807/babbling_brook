"""Editor composition root: Pygame input/timing, MVU, and PPM persistence."""
import argparse
from dataclasses import replace
from math import pi
from pathlib import Path

import moderngl
import pygame

from ..adapter.PygameUiView import PygameUiView
from ..adapter.PygameImages import PygameImages
from ..adapter.PygameMessageQueue import PygameMessageQueue
from ..codec.GameStateCodec import PluginStringCodec
from ..codec.map.MapCodec import MapCodec
from ..codec.map.ObjectPlacementCodec import ObjectPlacementCodec
from ..messages import KeyboardAction, KeyboardMessage, KeyboardModifiers
from .EditorFiles import EditorFiles
from ..update.CursorUpdater import CursorUpdater
from .EditorUpdater import EditorUpdater
from .AppHistoryTraversal import AppHistoryTraversal
from ..update.LookUpdater import LockedLookUpdater, DirectLookUpdater
from ..update.VectorUpdater import BoundedVectorUpdater, VectorKeysUpdater, VectorMouseUpdater
from ..view.Textures import Textures
from ..model.query.LightQuery import LightQuery
from ..model.system.CycleSystem import CycleSystem
from ..view.program.BillboardProgram import BillboardProgram
from ..view.program.HighlightProgram import HighlightProgram
from ..view.program.TileProgram import TileProgram
from ..view.program.UiProgram import UiProgram
from .EditorView import EditorView
from ..view.view.TileView import TileView
from ..view.view.BoxView import BoxView


def make_updater(map_codec, object_palette):
    # Keep keyboard look identical to the regular game; only mouse look is free.
    keylook = LockedLookUpdater(
        BoundedVectorUpdater(VectorKeysUpdater(*'ijkl', magnitude=(pi/2, pi/6)),
                             y0=pi/6, y1=pi/3),
        tuple(pi/4 + i*pi/2 for i in range(4)), (pi/6, pi/3),
    )
    return EditorUpdater(map_codec, object_palette,
            CursorUpdater(VectorKeysUpdater(*'wasd')),
            DirectLookUpdater(BoundedVectorUpdater(VectorMouseUpdater(-.01), y0=0, y1=pi/2)),
            keylook,
            AppHistoryTraversal(max_history_size=100), 
            CycleSystem())


def main(argv=None):
    parser = argparse.ArgumentParser(description='Babbling Brook level editor')
    parser.add_argument('ppm', type=Path, help='Text P3 PPM level to edit')
    parser.add_argument('--game', type=Path, help='Game definition/placements file (default: data/world.game)')
    args = parser.parse_args(argv)
    filename = args.ppm.resolve()
    root = Path(__file__).resolve().parents[2]
    data = root / 'data'
    game_filename = (args.game or data / 'world.game').resolve()
    try:
        plugin = PluginStringCodec().decode(game_filename.read_text(encoding='utf-8'))
        if any(not 0 <= index <= 65535 for index in plugin.tile_palette):
            raise ValueError('Tile palette IDs must be between 0 and 65535')
        if any(not 1 <= index <= 65535 for index in plugin.object_palette):
            raise ValueError('Object palette IDs must be between 1 and 65535; zero means empty')
        map_codec = MapCodec(plugin.tile_palette, plugin.tiles)
        ObjectPlacementCodec(plugin.object_palette, None, box_archetypes=plugin.box_archetypes,
                             billboard_archetypes=plugin.billboard_archetypes)
        files = EditorFiles(map_codec, plugin.object_palette,
                            game_filename=game_filename, plugin=plugin)
        state = replace(files.load(filename), cycles=dict(plugin.cycles))
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'Cannot open level: {error}\n')

    light_query = LightQuery(full_moon_color=.15, sun_color=1)
    gl = textures = view = None
    try:
        pygame.display.init()
        pygame.font.init()
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        pygame.display.set_mode(state.viewport, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
        gl = moderngl.create_context(require=330)
        gl.screen.use()
        textures = Textures(gl, PygameImages(root / 'texture'))
        view = EditorView(TileView(TileProgram(gl, textures)), BillboardProgram(gl, textures),
                          HighlightProgram(gl),
                          PygameUiView(UiProgram(gl)), plugin.billboard_archetypes,
                          filename.name, map_codec, plugin.object_palette,
                          BoxView(TileProgram(gl, textures)), plugin.box_archetypes)
        updater = make_updater(map_codec, plugin.object_palette)
        queue = PygameMessageQueue(monitored_keys='wasdzq')
        clock = pygame.time.Clock()
        while state.running:
            seconds = min(clock.tick(60) / 1000.0, .25)
            messages = queue.poll()
            for message in messages:
                if (isinstance(message, KeyboardMessage) and message.action == KeyboardAction.PRESS
                        and (message.key == 'f5' or message.key == 's'
                             and message.modifiers & KeyboardModifiers.CTRL)):
                    try:
                        state = files.save(filename, state)
                        state = replace(state, dirty=False, quit_requested=False,
                                        message=f'Saved {filename.name} and {game_filename.name}.')
                    except (OSError, ValueError) as error:
                        state = replace(state, message=f'Save failed: {error}')
                else:
                    state = updater.update(state, message)
                if not state.running:
                    break
            held = [message for message in messages
                    if isinstance(message, KeyboardMessage) and message.action == KeyboardAction.REPEAT]
            state = updater.step(state, seconds, held)
            light = light_query.query(state.cycles)
            pygame.display.set_caption(f'Level editor - {filename.name}{" *" if state.dirty else ""}')
            gl.viewport = (0, 0, *state.viewport)
            gl.fbo.depth_mask = True
            gl.clear(*light.background, 1, depth=1)
            view.draw(state, light)
            pygame.display.flip()
    finally:
        if view is not None:
            view.release()
        if textures is not None:
            textures.release()
        if gl is not None:
            gl.release()
        pygame.quit()


if __name__ == '__main__':
    main()
