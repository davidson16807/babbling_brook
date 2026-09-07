# HUMAN VETTED

from struct import pack

from pyglm import glm
import moderngl as gl

from ..Textures import Textures
from .ViewState import ViewState

"""
`BillboardProgram` renders a swarm of textured cylindrical billboards represented through primitives
"""

class BillboardProgram:
    VERTEX_SHADER = """#version 330 core
uniform mat4 clip_from_world;
uniform vec3 camera_right;
in vec2 in_corner;
in vec3 in_origin;
in vec2 in_size;
in vec4 in_uv_rect;
in float in_mirror;
out vec2 uv;
void main() {
    vec3 position = in_origin + camera_right * ((in_corner.x - 0.5) * in_size.x)
                              + vec3(0.0, 0.0, in_corner.y * in_size.y);
    gl_Position = clip_from_world * vec4(position, 1.0);
    float u = mix(in_corner.x, 1.0 - in_corner.x, in_mirror);
    uv = mix(in_uv_rect.xy, in_uv_rect.zw, vec2(u, in_corner.y));
}
"""

    FRAGMENT_SHADER = """#version 330 core
uniform sampler2D image;
in vec2 uv;
out vec4 color;
void main() {
    color = texture(image, uv);
    if (color.a < 0.5) discard;
}
"""

    def __init__(self, gl, textures: Textures):
        self.gl = gl
        self.program = gl.program(
            vertex_shader=self.VERTEX_SHADER,
            fragment_shader=self.FRAGMENT_SHADER
        )
        self.textures = textures
        self.quad = gl.buffer(b"".join(value.to_bytes() for value in [glm.vec2(0, 0), glm.vec2(1, 0), glm.vec2(1, 1),
            glm.vec2(0, 0), glm.vec2(1, 1), glm.vec2(0, 1)]))
        self.buffers = [gl.buffer(reserve=16) for _ in range(4)]
        self.vao = gl.vertex_array(self.program, [(self.quad, "2f", "in_corner"),
            (self.buffers[0], "3f /i", "in_origin"), (self.buffers[1], "2f /i", "in_size"),
            (self.buffers[2], "4f /i", "in_uv_rect"), (self.buffers[3], "1f /i", "in_mirror")])

        self.released = False

    def draw(self, 
        textures: tuple[str, ...],
        origin: tuple[glm.vec3, ...],
        size: tuple[glm.vec2, ...],
        uv_rect: tuple[glm.vec4, ...],
        mirrored: tuple[bool, ...],
        view: ViewState
    ) -> None:
        if self.released or not origin:
            return
        if len({len(values) for values in (textures, origin, size, uv_rect, mirrored)}) != 1:
            raise ValueError("Billboard attributes must have equal lengths")
        self.gl.enable_only(gl.DEPTH_TEST | gl.BLEND)
        self.gl.fbo.depth_mask = True
        self.gl.depth_func = "<="
        self.gl.blend_func = gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA
        self.program["clip_from_world"].write(view.clip_from_world.to_bytes())
        self.program["camera_right"].value = tuple(view.camera_right)
        self.program["image"].value = 0

        # The view supplies back-to-front instances. Keep that order when textures differ.
        for i, texture in enumerate(textures):
            self.textures.get(texture).use(0)
            values = (origin[i].to_bytes(), size[i].to_bytes(), uv_rect[i].to_bytes(),
                      pack("f", float(mirrored[i])))
            for buffer, data in zip(self.buffers, values):
                buffer.write(data)
            self.vao.render(gl.TRIANGLES, vertices=6, instances=1)

    def release(self):
        if self.released:
            return
        self.released = True
        self.vao.release()
        for buffer in self.buffers:
            buffer.release()
        self.quad.release()
        self.program.release()
