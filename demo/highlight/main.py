"""Display HighlightProgram over the Babbling Brook terrain.

Run from the repository root with:

    python demo/highlight/main.py

Close the window or press Escape to exit.
"""
from importlib.util import module_from_spec, spec_from_file_location
from math import pi, sin
from pathlib import Path
import sys
from time import perf_counter

import moderngl
import pygame
from pyglm import glm


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

from babbling_brook.adapter.PygameImages import PygameImages
from babbling_brook.codec.GameStateCodec import PluginStringCodec
from babbling_brook.model.GameFiles import GameFiles
from babbling_brook.model.plugin.PluginOps import PluginOps
from babbling_brook.view.Textures import Textures
from babbling_brook.view.program.HighlightProgram import HighlightProgram
from babbling_brook.view.program.TileProgram import TileProgram
from babbling_brook.view.program.ViewState import ViewState
from babbling_brook.view.view.TileView import TileView


WINDOW_SIZE = 960, 640


def view_state(map_):
    target_xy = glm.vec2(8.5, 8.5)
    target = glm.vec3(target_xy, map_.height(target_xy))
    forward = glm.normalize(glm.vec3(-1, -1, -0.72))
    aspect = WINDOW_SIZE[0] / WINDOW_SIZE[1]
    scale = 6.5
    projection = glm.ortho(-scale * aspect, scale * aspect, -scale, scale, .1, 100)
    return ViewState(
        projection * glm.lookAt(target - forward * 30, target, glm.vec3(0, 0, 1)),
        glm.normalize(glm.cross(forward, glm.vec3(0, 0, 1))),
    )


def main():
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(
        pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
    )
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
    pygame.display.set_mode(WINDOW_SIZE, pygame.OPENGL | pygame.DOUBLEBUF)
    pygame.display.set_caption(
        'HighlightProgram demo — cyan range, amber selection, red blocked — Esc closes'
    )
    context = moderngl.create_context(require=330)

    files = GameFiles(PluginOps(), PluginStringCodec())
    game = files.load(ROOT / 'data' / 'world.ppm', [ROOT / 'data' / 'world.game'])
    textures = Textures(context, PygameImages(ROOT / 'data' / 'texture'))
    terrain = TileView(TileProgram(context, textures))
    highlights = HighlightProgram(context)

    movement = tuple(
        (x, y)
        for y in range(5, 12)
        for x in range(5, 12)
        if 1 <= abs(x - 8) + abs(y - 8) <= 3
    )
    blocked = ((5, 8), (8, 5), (11, 8), (8, 11))
    selected = ((9, 7),)
    coordinates = movement + blocked + selected
    heights = tuple(game.map.corner_heights(coordinate) for coordinate in coordinates)
    view = view_state(game.map)

    started = perf_counter()
    clock = pygame.time.Clock()
    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            context.viewport = (0, 0, *WINDOW_SIZE)
            context.fbo.depth_mask = True
            context.clear(.11, .16, .18, 1, depth=1)
            terrain.draw(game.map, view)

            pulse = .45 + .18 * sin((perf_counter() - started) * 2 * pi)
            colors = (
                ((.05, .65, 1.0, .30),) * len(movement)
                + ((1.0, .12, .08, .48),) * len(blocked)
                + ((1.0, .72, .05, pulse),)
            )
            highlights.draw(coordinates, heights, colors, view)

            pygame.display.flip()
            clock.tick(60)
    finally:
        highlights.release()
        terrain.release()
        textures.release()
        context.release()
        pygame.quit()


if __name__ == '__main__':
    main()
