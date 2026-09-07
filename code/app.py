"""Desktop composition root: Pygame window/timing, internal messages, MVU."""
import argparse
from dataclasses import replace
from pathlib import Path

from . import APPLICATION_TITLE
from .game import load_game, save_game
from .messages import KeyboardMessage, KeyboardAction, TickMessage
from .update.GameUpdater import default_updater


def main():
    parser = argparse.ArgumentParser(description=APPLICATION_TITLE)
    parser.add_argument('--data', type=Path, default=Path('data'), help='Directory containing world.ppm, world.game, and textures/')
    parser.add_argument('--save', type=Path, default=Path('saves/slot.sav'), help='F5/F9 save slot')
    parser.add_argument('--load', action='store_true', help='Resume the save slot at startup')
    parser.add_argument('--frames', type=int, help='Exit after this many frames (smoke testing)')
    parser.add_argument('--headless', action='store_true', help='Render offscreen with EGL (requires EGL support)')
    parser.add_argument('--screenshot', type=Path, help='Write the final rendered frame to a PNG')
    args = parser.parse_args()
    if args.frames is not None and args.frames <= 0:
        parser.error('--frames must be positive')
    if args.headless and args.frames is None:
        args.frames = 1
    try:
        model = load_game(args.data, args.save if args.load else None)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Cannot load game: {error}\n')

    import moderngl
    import pygame
    from .adapters.PygameMessageQueue import PygameMessageQueue
    from .adapters.PygameImages import PygameImages
    from .adapters.PygameUiView import PygameUiView
    from .view.Textures import Textures
    from .view.programs.TileProgram import TileProgram
    from .view.programs.BillboardProgram import BillboardProgram
    from .view.programs.UiProgram import UiProgram
    from .view.views.TileView import TileView
    from .view.views.BillboardView import BillboardView
    from .view.views.GameView import GameView

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
            queue = PygameMessageQueue()
        textures = Textures(gl, PygameImages(args.data / 'textures'))
        # Validate and create the finite texture set before entering the render loop.
        names = {item.texture for item in model.archetypes.tiles.values()} | {item.texture for item in model.archetypes.objects.values()}
        for character in model.archetypes.characters.values():
            for animation in (character.standing, character.walking, character.running):
                if animation:
                    names.update(texture for direction in animation.directions for texture in direction.textures)
        for name in sorted(names):
            textures.get(name)
        view = GameView(TileView(TileProgram(gl, textures)),
                        BillboardView(BillboardProgram(gl, textures)), PygameUiView(UiProgram(gl)))
        updater, clock, accumulator, frames = default_updater(), pygame.time.Clock(), 0.0, 0
        while model.running and (args.frames is None or frames < args.frames):
            elapsed = 1 / 60 if args.headless else min(clock.tick(60) / 1000.0, .25)
            for message in queue.poll():
                if isinstance(message, KeyboardMessage) and message.action == KeyboardAction.PRESS and message.key in ('f5', 'f9'):
                    try:
                        if message.key == 'f5':
                            save_game(args.save, model)
                            model = replace(model, message='Game saved.')
                        else:
                            restored = load_game(args.data, args.save)
                            model = replace(restored, viewport=model.viewport, camera=model.camera, message='Game loaded.')
                            accumulator = 0.0
                    except (OSError, ValueError) as error:
                        model = replace(model, message=f'Save/load failed: {error}')
                else:
                    model = updater.update(model, message)
            accumulator += elapsed
            while accumulator >= 1 / 120:
                model = updater.update(model, TickMessage(1 / 120))
                accumulator -= 1 / 120
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
