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
        self.program = gl.program(
            vertex_shader=(shader_directory / "ui.vert").read_text(),
            fragment_shader=(shader_directory / "ui.frag").read_text()
        )
        self.quad = gl.buffer(b"".join(value.to_bytes() for value in
            [glm.vec2(0, 0), glm.vec2(1, 0), glm.vec2(1, 1),
             glm.vec2(0, 0), glm.vec2(1, 1), glm.vec2(0, 1)]
        ))
        self.vao = gl.vertex_array(self.program, [(self.quad, "2f", "in_corner")])
        self.textures = {}
        self.released = False

    def draw(self, 
        viewport: tuple[int, int],
        keys: tuple[str, ...],
        rects: tuple[glm.vec4, ...],  # left, top, width, height in viewport pixels
        sizes: tuple[tuple[int, int], ...],
        rgba: tuple[bytes, ...],  # bottom-to-top rows for OpenGL
    ) -> None:
        if self.released:
            return
        if len({len(values) for values in (keys, rects, sizes, rgba)}) != 1:
            raise ValueError("UI attributes must have equal lengths")
        self.gl.enable_only(gl.BLEND)
        self.gl.fbo.depth_mask = False
        self.gl.blend_func = gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA
        self.program["viewport"].value = viewport
        self.program["image"].value = 0

        for key, rect, size, pixels in zip(keys, rects, sizes, rgba):
            cached = self.textures.get(key)
            if cached is None or cached[0] != size:
                if cached is not None:
                    cached[1].release()
                texture = self.gl.texture(size, 4, pixels)
                texture.filter = (gl.NEAREST, gl.NEAREST)
                self.textures[key] = (size, texture)
            else:
                texture = cached[1]
                texture.write(pixels)
            texture.use(0)
            self.program["rect"].value = tuple(rect)
            self.vao.render(gl.TRIANGLES, vertices=6)

    def release(self):
        if self.released:
            return
        self.released = True
        for _, texture in self.textures.values():
            texture.release()
        self.textures.clear()
        self.vao.release()
        self.quad.release()
        self.program.release()
