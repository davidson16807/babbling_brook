# HUMAN VETTED

from collections.abc import Sequence

from pyglm import glm
import moderngl as gl


"""
`TileProgram` renders 2d ui elements on the screen

There is no game logic or entity lookup here. Each draw establishes its own
required depth/blend state. release() is explicit resource lifecycle management.
"""

class UiProgram:
    VERTEX_SHADER = """#version 330 core
uniform vec2 viewport;
uniform vec4 rect;
in vec2 in_corner;
out vec2 uv;
void main() {
    vec2 pixel = rect.xy + in_corner * rect.zw;
    gl_Position = vec4(pixel.x / viewport.x * 2.0 - 1.0, 1.0 - pixel.y / viewport.y * 2.0, 0.0, 1.0);
    uv = vec2(in_corner.x, 1.0 - in_corner.y);
}
"""

    FRAGMENT_SHADER = """#version 330 core
uniform sampler2D image;
in vec2 uv;
out vec4 color;
void main() {
    color = texture(image, uv);
}
"""

    def __init__(self, gl):
        self.gl = gl
        self.program = gl.program(
            vertex_shader=self.VERTEX_SHADER,
            fragment_shader=self.FRAGMENT_SHADER
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
