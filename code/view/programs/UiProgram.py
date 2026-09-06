# HUMAN VETTED

from pathlib import Path

from collections.abc import Sequence

from pyglm import glm
import moderngl as gl


"""
`TileProgram` renders 2d ui elements on the screen

There is no game logic or entity lookup here. Each draw establishes its own
required depth/blend state. release() is explicit resource lifecycle management.
"""

class UiProgram:
    def __init__(self, gl, shader_directory: Path):
        self.gl = gl
        self.program = ctx.program(
            vertex_shader=(shader_directory / "tile.vert").read_text(),
            fragment_shader=(shader_directory / "tile.frag").read_text()
        )
        self.quad = gl.buffer(memoryview(glm.array(
            [glm.vec2(0, 0), glm.vec2(1, 0), glm.vec2(1, 1),
             glm.vec2(0, 0), glm.vec2(1, 1), glm.vec2(0, 1)]
        )))
        self.vao = gl.vertex_array(self.program, [(self.quad, "2f", "in_corner")])
        self.textures = {}

    def draw(self, 
        viewport: tuple[int, int],
        key: str,
        rect: glm.vec4,  # left, top, width, height in viewport pixels
        size: tuple[int, int],
        rgba: bytes,  # bottom-to-top rows for OpenGL
    ) -> None:
        self.gl.enable_only(gl.BLEND)
        self.gl.depth_mask = False
        self.gl.blend_func = gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA
        self.program["viewport"].value = viewport
        self.program["image"].value = 0

        ...

    def release(self):
        for _, texture in self.textures.values():
            texture.release()
        self.textures.clear()
        self.vao.release()
        self.quad.release()
        self.program.release()
