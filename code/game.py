# HUMAN VETTED

"""Desktop composition root: Pygame window/timing, internal messages, MVU."""
import argparse
from dataclasses import replace
from math import pi
from pathlib import Path

import moderngl
import pygame

from .adapter.PygameMessageQueue import PygameMessageQueue
from .adapter.PygameImages import PygameImages
from .adapter.PygameUiView import PygameUiView
from .view.Textures import Textures
from .view.program.TileProgram import TileProgram
from .view.program.BillboardProgram import BillboardProgram
from .view.program.UiProgram import UiProgram
from .view.view.TileView import TileView
from .view.view.BillboardView import BillboardView
from .view.view.GameView import GameView

from .update.GameUpdater import GameUpdater
from .update.LookUpdater import (BoundedVectorUpdater, LockedLookUpdater,
                                 VectorKeysUpdater, VectorMouseUpdater)
from .update.MovementUpdater import MovementUpdater
from .update.DirectionalKeysUpdater import DirectionalKeysUpdater
from .update.actions import *

from .model.query.CollisionQuery import CollisionQuery
from .model.query.InteractionQuery import InteractionQuery
from .model.system.GravitySystem import GravitySystem
from .model.system.CharacterAnimationSystem import CharacterAnimationSystem
from .model.plugin.PluginOps import PluginOps
from .codec.GameStateCodec import PluginStringCodec

from . import APPLICATION_TITLE
from .model.GameFiles import GameFiles
from .messages import KeyboardMessage, KeyboardAction

def main(argv=None):
    parser = argparse.ArgumentParser(description=APPLICATION_TITLE)
    parser.add_argument('game_files', nargs='*', type=Path, help='Plugin files; only .game and .mod files are loaded')
    parser.add_argument('--data', type=Path, default=Path('data'), help='Directory containing world.ppm, world.game, and texture/')
    parser.add_argument('--map', type=Path, help='PPM map file (defaults to DATA/world.ppm)')
    parser.add_argument('--save', type=Path, default=Path('save/slot.sav'), help='F5/F9 save slot')
    parser.add_argument('--load', action='store_true', help='Resume the save slot at startup')
    parser.add_argument('--frames', type=int, help='Exit after this many frames (smoke testing)')
    parser.add_argument('--headless', action='store_true', help='Render offscreen with EGL (requires EGL support)')
    parser.add_argument('--screenshot', type=Path, help='Write the final rendered frame to a PNG')
    args = parser.parse_args(argv)
    if args.frames is not None and args.frames <= 0:
        parser.error('--frames must be positive')
    if args.headless and args.frames is None:
        args.frames = 1
    if args.game_files and not args.game_files:
        parser.error('at least one .game or .mod file is required')
    if not args.game_files:
        args.game_files = [args.data / 'world.game']
    map_filename = args.map or args.data / 'world.ppm'
    game_files = GameFiles(PluginOps(), PluginStringCodec())
    try:
        model = game_files.load(map_filename, args.game_files, args.save if args.load else None)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Cannot load game: {error}\n')
    gl = view = textures = framebuffer = None
    try:
        pygame.font.init()
        if args.headless:
            gl = moderngl.create_standalone_context(require=330, backend='egl')
            framebuffer = gl.simple_framebuffer(model.viewport)
            framebuffer.use()
            queue = PygameMessageQueue(lambda: ())
        else:
            pygame.display.init()
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
            pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
            pygame.display.set_mode(model.viewport, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
            pygame.display.set_caption(APPLICATION_TITLE)
            gl = moderngl.create_context(require=330)
            gl.screen.use()
            queue = PygameMessageQueue(
                monitored_keys=[*'wasd', 'shift', 'right shift']
            )
        textures = Textures(gl, PygameImages(args.data / 'texture'))
        # Validate and create the finite texture set before entering the render loop.
        names = {
            texture
            for item in model.archetypes.tiles.values()
            for texture in (item.top_texture, item.side_texture)
        } | {item.texture for item in model.archetypes.objects.values()}
        names.update(
            texture
            for texture, _ in model.character_animation_frames.values()
        )
        for name in sorted(names):
            textures.get(name)
        view = GameView(TileView(TileProgram(gl, textures)),
                        BillboardView(BillboardProgram(gl, textures)), 
                        PygameUiView(UiProgram(gl)))
        movement = MovementUpdater(CollisionQuery(), DirectionalKeysUpdater(*'wasd'))
        gravity = GravitySystem()
        animations = CharacterAnimationSystem()
        azimuths = tuple(pi/4 + index*pi/2 for index in range(4))
        elevations = (pi/6, pi/3)
        mouselook = LockedLookUpdater(
            BoundedVectorUpdater(
                VectorMouseUpdater(-.01),
                y0=pi/6,
                y1=pi/3,
            ),
            azimuths,
            elevations,
        )
        keylook = LockedLookUpdater(
            BoundedVectorUpdater(
                VectorKeysUpdater(*'ijkl', magnitude=(pi/2, pi/6)),
                y0=pi/6,
                y1=pi/3,
            ),
            azimuths,
            elevations,
        )
        updater = GameUpdater(
            mouselook,
            keylook,
            InteractionQuery(),
            ActionRegistry({'collect_apple': collect('apple'), 'collect_stick': collect('stick'), 'greet': greet})
        )
        clock = pygame.time.Clock()
        accumulator = 0.0
        frames = 0
        while model.running and (args.frames is None or frames < args.frames):
            elapsed = 1 / 60 if args.headless else min(clock.tick(60) / 1000.0, .25)
            messages = queue.poll()
            pressed_keys = frozenset(
                message.key for message in messages
                if isinstance(message, KeyboardMessage) and message.action == KeyboardAction.REPEAT
            )
            for message in messages:
                if isinstance(message, KeyboardMessage) and message.action == KeyboardAction.PRESS and message.key in ('f5', 'f9'):
                    try:
                        if message.key == 'f5':
                            game_files.save(args.save, model)
                            model = replace(model, message='Game saved.')
                        else:
                            restored = game_files.load(map_filename, args.game_files, args.save)
                            model = replace(restored, viewport=model.viewport, camera=model.camera, message='Game loaded.')
                            accumulator = 0.0
                    except (OSError, ValueError) as error:
                        model = replace(model, message=f'Save/load failed: {error}')
                else:
                    model = updater.update(model, message)
            accumulator += elapsed
            while accumulator >= 1 / 120:
                seconds = 1 / 120
                model = movement.update(model, seconds, pressed_keys)
                instances = model.instances
                placements, physics = gravity.step(
                    instances.placements, instances.physics, model.map, seconds)
                characters = animations.step(instances.characters, seconds)
                model = replace(
                    model,
                    instances=replace(
                        instances,
                        placements=placements,
                        physics=physics,
                        characters=characters,
                    ),
                )
                accumulator -= seconds
            gl.viewport = (0, 0, *model.viewport)
            gl.fbo.depth_mask = True
            gl.clear(.16, .23, .25, 1.0, depth=1.0)
            view.draw(model)
            frames += 1
            if args.screenshot and (not model.running or args.frames is not None and frames >= args.frames):
                target = framebuffer if framebuffer is not None else gl.screen
                pixels = target.read(viewport=(0, 0, *model.viewport), components=3, alignment=1)
                surface = pygame.image.frombytes(pixels, model.viewport, 'RGB', True)
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                pygame.image.save(surface, str(args.screenshot))
            if not args.headless:
                pygame.display.flip()
    finally:
        if view is not None:
            view.release()
        if textures is not None:
            textures.release()
        if framebuffer is not None:
            framebuffer.release()
        if gl is not None:
            gl.release()
        pygame.quit()


if __name__ == '__main__':
    main()
