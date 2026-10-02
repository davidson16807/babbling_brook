# HUMAN VETTED

from struct import pack

from pyglm import glm
import moderngl as gl

from ..Textures import Textures
from .ViewState import ViewState
from .Atmosphere import ATMOSPHERE_SHADER, write_atmosphere

"""
`BillboardProgram` renders a swarm of textured cylindrical billboards represented through primitives
"""

class BillboardProgram:
    ELEMENT_POSITIONS = (
        (0, 0), (1, 0), (1, 1),
        (0, 0), (1, 1), (0, 1),
    )
    ELEMENT_UVS = (
        (0, 0), (1, 0), (1, 1),
        (0, 0), (1, 1), (0, 1),
    )

    VERTEX_SHADER = """#version 330 core
uniform mat4 clip_from_world;
uniform vec3 camera_right;
in vec2 element_position;
in vec2 element_uv;
in vec3 origin;
in vec2 size;
in vec4 uv_rect;
in float mirrored;
out vec2 uv;
out vec3 world_position;
void main() {
    vec3 position = origin + camera_right * ((element_position.x - 0.5) * size.x)
                           + vec3(0.0, 0.0, element_position.y * size.y);
    gl_Position = clip_from_world * vec4(position, 1.0);
    world_position = position;
    float u = mix(element_uv.x, 1.0 - element_uv.x, mirrored);
    uv = mix(uv_rect.xy, uv_rect.zw, vec2(u, element_uv.y));
}
"""

    FRAGMENT_SHADER = """#version 330 core
uniform sampler2D image;
uniform vec3 light_direction;
uniform vec3 light_color;
uniform vec3 camera_right;
in vec2 uv;
in vec3 world_position;
out vec4 color;
""" + ATMOSPHERE_SHADER + """
void main() {
    color = texture(image, uv);
    if (color.a < 0.5) discard;
    vec3 normal = normalize(cross(camera_right, vec3(0.0, 0.0, 1.0)));
    // A sprite is two-sided; use the lit side of its vertical plane.
    float lighting = 0.60 + 0.40 * abs(dot(normal, normalize(light_direction)));
    color.rgb = atmospheric_color(color.rgb * lighting * light_color, world_position);
}
"""

    def __init__(self, gl, textures: Textures):
        self.gl = gl
        self.program = gl.program(
            vertex_shader=self.VERTEX_SHADER,
            fragment_shader=self.FRAGMENT_SHADER
        )
        self.textures = textures
        self.element_position_buffer = gl.buffer(pack(
            f"{2 * len(self.ELEMENT_POSITIONS)}f",
            *(value for position in self.ELEMENT_POSITIONS for value in position)
        ))
        self.element_uv_buffer = gl.buffer(pack(
            f"{2 * len(self.ELEMENT_UVS)}f",
            *(value for uv in self.ELEMENT_UVS for value in uv)
        ))
        self.origin_buffer = gl.buffer(reserve=16)
        self.size_buffer = gl.buffer(reserve=16)
        self.uv_rect_buffer = gl.buffer(reserve=16)
        self.mirrored_buffer = gl.buffer(reserve=16)
        self.vao = gl.vertex_array(self.program, [
            (self.element_position_buffer, "2f", "element_position"),
            (self.element_uv_buffer, "2f", "element_uv"),
            (self.origin_buffer, "3f /i", "origin"),
            (self.size_buffer, "2f /i", "size"),
            (self.uv_rect_buffer, "4f /i", "uv_rect"),
            (self.mirrored_buffer, "1f /i", "mirrored"),
        ])

        self.released = False

    def draw(self, 
        texture: str,
        origins: tuple[glm.vec3, ...],
        sizes: tuple[glm.vec2, ...],
        uv_rects: tuple[glm.vec4, ...],
        mirrored: tuple[bool, ...],
        view: ViewState
    ) -> None:
        if self.released or not origins:
            return
        if len({len(values) for values in (origins, sizes, uv_rects, mirrored)}) != 1:
            raise ValueError("Billboard attributes must have equal lengths")
        self.gl.enable_only(gl.DEPTH_TEST)
        self.gl.fbo.depth_mask = True
        self.gl.depth_func = "<="
        self.program["clip_from_world"].write(view.clip_from_world.to_bytes())
        self.program["camera_right"].value = tuple(view.camera_right)
        self.program["light_direction"].value = tuple(view.light_direction)
        self.program["light_color"].value = tuple(view.light_color)
        write_atmosphere(self.program, view)
        self.program["image"].value = 0

        self.textures.get(texture).use(0)

        origin_data = b"".join(value.to_bytes() for value in origins)
        if self.origin_buffer.size < len(origin_data):
            self.origin_buffer.orphan(len(origin_data))
        self.origin_buffer.write(origin_data)

        size_data = b"".join(value.to_bytes() for value in sizes)
        if self.size_buffer.size < len(size_data):
            self.size_buffer.orphan(len(size_data))
        self.size_buffer.write(size_data)

        uv_rect_data = b"".join(value.to_bytes() for value in uv_rects)
        if self.uv_rect_buffer.size < len(uv_rect_data):
            self.uv_rect_buffer.orphan(len(uv_rect_data))
        self.uv_rect_buffer.write(uv_rect_data)

        mirrored_data = pack(f"{len(mirrored)}f", *(float(value) for value in mirrored))
        if self.mirrored_buffer.size < len(mirrored_data):
            self.mirrored_buffer.orphan(len(mirrored_data))
        self.mirrored_buffer.write(mirrored_data)

        self.vao.render(
            gl.TRIANGLES,
            vertices=len(self.ELEMENT_POSITIONS),
            instances=len(origins)
        )

    def release(self):
        if self.released:
            return
        self.released = True
        self.vao.release()
        self.element_position_buffer.release()
        self.element_uv_buffer.release()
        self.origin_buffer.release()
        self.size_buffer.release()
        self.uv_rect_buffer.release()
        self.mirrored_buffer.release()
        self.program.release()
