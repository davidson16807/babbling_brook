# HUMAN VETTED

from struct import pack

from pyglm import glm
import moderngl as gl


"""
`TileProgram` renders 2d ui elements on the screen

There is no game logic or entity lookup here. Each draw establishes its own
required depth/blend state. release() is explicit resource lifecycle management.
"""

class UiProgram:
    ELEMENT_POSITIONS = (
        (0, 0), (1, 0), (1, 1),
        (0, 0), (1, 1), (0, 1),
    )
    ELEMENT_UVS = (
        (0, 1), (1, 1), (1, 0),
        (0, 1), (1, 0), (0, 0),
    )

    VERTEX_SHADER = """#version 330 core
uniform vec2 viewport;
in vec2 element_position;
in vec2 element_uv;
in vec4 rect;
in vec4 uv_rect;
out vec2 uv;
void main() {
    vec2 pixel = rect.xy + element_position * rect.zw;
    gl_Position = vec4(pixel.x / viewport.x * 2.0 - 1.0, 1.0 - pixel.y / viewport.y * 2.0, 0.0, 1.0);
    uv = mix(uv_rect.xy, uv_rect.zw, element_uv);
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
        self.element_position_buffer = gl.buffer(pack(
            f"{2 * len(self.ELEMENT_POSITIONS)}f",
            *(value for position in self.ELEMENT_POSITIONS for value in position)
        ))
        self.element_uv_buffer = gl.buffer(pack(
            f"{2 * len(self.ELEMENT_UVS)}f",
            *(value for uv in self.ELEMENT_UVS for value in uv)
        ))
        self.rect_buffer = gl.buffer(reserve=16)
        self.uv_rect_buffer = gl.buffer(reserve=16)
        self.vao = gl.vertex_array(self.program, [
            (self.element_position_buffer, "2f", "element_position"),
            (self.element_uv_buffer, "2f", "element_uv"),
            (self.rect_buffer, "4f /i", "rect"),
            (self.uv_rect_buffer, "4f /i", "uv_rect"),
        ])
        self.textures = {}
        self.released = False

    def draw(self, 
        viewport: tuple[int, int],
        texture_key: str,
        size: tuple[int, int],
        rgba: bytes,  # bottom-to-top rows for OpenGL
        rects: tuple[glm.vec4, ...],  # left, top, width, height in viewport pixels
        uv_rects: tuple[glm.vec4, ...],
    ) -> None:
        if self.released or not rects:
            return
        if len(rects) != len(uv_rects):
            raise ValueError("UI attributes must have equal lengths")
        self.gl.enable_only(gl.BLEND)
        self.gl.fbo.depth_mask = False
        self.gl.blend_func = gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA
        self.program["viewport"].value = viewport
        self.program["image"].value = 0

        cached = self.textures.get(texture_key)
        if cached is None or cached[0] != size:
            if cached is not None:
                cached[1].release()
            texture = self.gl.texture(size, 4, rgba)
            texture.filter = (gl.NEAREST, gl.NEAREST)
            texture.repeat_x = False
            texture.repeat_y = False
            self.textures[texture_key] = (size, texture)
        else:
            texture = cached[1]
            texture.write(rgba)
        texture.use(0)

        rect_data = b"".join(rect.to_bytes() for rect in rects)
        if self.rect_buffer.size < len(rect_data):
            self.rect_buffer.orphan(len(rect_data))
        self.rect_buffer.write(rect_data)

        uv_rect_data = b"".join(uv_rect.to_bytes() for uv_rect in uv_rects)
        if self.uv_rect_buffer.size < len(uv_rect_data):
            self.uv_rect_buffer.orphan(len(uv_rect_data))
        self.uv_rect_buffer.write(uv_rect_data)

        self.vao.render(
            gl.TRIANGLES,
            vertices=len(self.ELEMENT_POSITIONS),
            instances=len(rects)
        )

    def release(self):
        if self.released:
            return
        self.released = True
        for _, texture in self.textures.values():
            texture.release()
        self.textures.clear()
        self.vao.release()
        self.element_position_buffer.release()
        self.element_uv_buffer.release()
        self.rect_buffer.release()
        self.uv_rect_buffer.release()
        self.program.release()
