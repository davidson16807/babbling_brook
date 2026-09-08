# HUMAN VETTED

from struct import pack

import moderngl as gl
from pyglm import glm

from .ViewState import ViewState
from ..Textures import Textures


"""
`TileProgram` renders a swarm of textured 3D tiles represented through primitives

There is no game logic or entity lookup here. Each draw establishes its own
required depth/blend state. release() is explicit resource lifecycle management.
"""

class TileProgram:
    # Ten triangles: two across the top, then two for west, east, south, north.
    # Position components select west/east, south/north, and bottom/top.
    ELEMENT_POSITIONS = (
        (0, 0, 1), (1, 0, 1), (1, 1, 1),
        (0, 0, 1), (1, 1, 1), (0, 1, 1),
        (0, 0, 1), (0, 1, 0), (0, 0, 0),
        (0, 0, 1), (0, 1, 1), (0, 1, 0),
        (1, 1, 1), (1, 0, 0), (1, 1, 0),
        (1, 1, 1), (1, 0, 1), (1, 0, 0),
        (1, 0, 1), (0, 0, 0), (1, 0, 0),
        (1, 0, 1), (0, 0, 1), (0, 0, 0),
        (0, 1, 1), (1, 1, 0), (0, 1, 0),
        (0, 1, 1), (1, 1, 1), (1, 1, 0),
    )
    ELEMENT_UVS = (
        (0, 0), (1, 0), (1, 1),
        (0, 0), (1, 1), (0, 1),
        (0, 1), (1, 0), (0, 0),
        (0, 1), (1, 1), (1, 0),
        (0, 1), (1, 0), (0, 0),
        (0, 1), (1, 1), (1, 0),
        (0, 1), (1, 0), (0, 0),
        (0, 1), (1, 1), (1, 0),
        (0, 1), (1, 0), (0, 0),
        (0, 1), (1, 1), (1, 0),
    )
    ELEMENT_NORMALS = tuple(
        vertex_normal
        for side_normal in (
            (0, 0, 1),
            (-1, 0, 0),
            (1, 0, 0),
            (0, -1, 0),
            (0, 1, 0),
        )
        for vertex_normal in (side_normal,)*6
    )

    VERTEX_SHADER = """#version 330 core
uniform mat4 clip_from_world;
in ivec3 element_position;
in vec2 element_uv;
in ivec3 element_normal;
in vec2 coordinate;
in mat2 heights;
out vec2 uv;
out float lighting;
flat out int fragment_is_top;

void main() {
    float height = element_position.z == 0
        ? 0.0
        : heights[element_position.x][element_position.y];
    vec3 position = vec3(coordinate + vec2(element_position.xy), height);

    vec3 southwest = vec3(0, 0, heights[0][0]);
    vec3 northwest = vec3(0, 1, heights[0][1]);
    vec3 southeast = vec3(1, 0, heights[1][0]);
    vec3 northeast = vec3(1, 1, heights[1][1]);
    fragment_is_top = element_normal.z;
    vec3 normal = fragment_is_top<0.? vec3(element_normal)
      : element_position.x > element_position.y?
            cross(southeast - southwest, northeast - southwest)
          : cross(northeast - southwest, northwest - southwest);

    gl_Position = clip_from_world * vec4(position, 1.0);
    lighting = 0.60 + 0.40 * max(dot(normalize(normal), normalize(vec3(-0.5, -0.7, 1.0))), 0.0);
    uv = element_uv;
}
"""

    FRAGMENT_SHADER = """#version 330 core
uniform sampler2D top_image;
uniform sampler2D side_image;
in vec2 uv;
in float lighting;
flat in int fragment_is_top;
out vec4 color;
void main() {
    vec3 texture_color;
    if (fragment_is_top == 1) {
        texture_color = texture(top_image, uv).rgb;
    } else {
        texture_color = texture(side_image, uv).rgb;
    }
    color = vec4(texture_color * lighting, 1.0);
}
"""

    def __init__(self, gl, textures: Textures):
        self.textures = textures
        self.gl = gl
        self.program = gl.program(
            vertex_shader=self.VERTEX_SHADER,
            fragment_shader=self.FRAGMENT_SHADER
        )
        self.element_position_buffer = gl.buffer(pack(
            f"{3 * len(self.ELEMENT_POSITIONS)}i",
            *(value for position in self.ELEMENT_POSITIONS for value in position)
        ))
        self.element_uv_buffer = gl.buffer(pack(
            f"{2 * len(self.ELEMENT_UVS)}f",
            *(value for uv in self.ELEMENT_UVS for value in uv)
        ))
        self.element_normal_buffer = gl.buffer(pack(
            f"{3 * len(self.ELEMENT_NORMALS)}i",
            *(value for normal in self.ELEMENT_NORMALS for value in normal)
        ))
        self.coordinate_buffer = gl.buffer(reserve=16)
        self.height_buffer = gl.buffer(reserve=16)
        self.vao = gl.vertex_array(self.program, [
            (self.element_position_buffer, "3i", "element_position"),
            (self.element_uv_buffer, "2f", "element_uv"),
            (self.element_normal_buffer, "3i", "element_normal"),
            (self.coordinate_buffer, "2f /i", "coordinate"),
            (self.height_buffer, "4f /i", "heights"),
        ])
        self.released = False

    def draw(self,
        top_texture: str,
        side_texture: str,
        coordinates: tuple[tuple[int, int], ...],
        heights: tuple[glm.mat2, ...],
        view: ViewState
    ) -> None:
        """Draw unit tiles from parallel coordinate and height-matrix collections.

        Matrix columns are west/east and rows are south/north.
        Sides extend from their top edge to the shader's fixed bottom height.
        Top triangles share the southwest–northeast diagonal.
        """
        if self.released:
            return
        if len(coordinates) != len(heights):
            raise ValueError("Tile coordinates and heights must have equal lengths")
        if not coordinates:
            return
        self.gl.enable_only(gl.DEPTH_TEST | gl.CULL_FACE)
        self.gl.front_face = "ccw"
        self.gl.cull_face = "back"
        self.gl.fbo.depth_mask = True
        self.gl.depth_func = "<="
        self.program["clip_from_world"].write(view.clip_from_world.to_bytes())
        self.program["top_image"].value = 0
        self.program["side_image"].value = 1

        self.textures.get(top_texture).use(0)
        self.textures.get(side_texture).use(1)
        coordinate_data = pack(f"{2 * len(coordinates)}f", *(value for pair in coordinates for value in pair))
        if self.coordinate_buffer.size < len(coordinate_data):
            self.coordinate_buffer.orphan(len(coordinate_data))
        self.coordinate_buffer.write(coordinate_data)

        height_data = b"".join(height.to_bytes() for height in heights)
        if self.height_buffer.size < len(height_data):
            self.height_buffer.orphan(len(height_data))
        self.height_buffer.write(height_data)

        # Two top triangles and two for each side.
        self.vao.render(gl.TRIANGLES, vertices=len(self.ELEMENT_POSITIONS), instances=len(coordinates))

    def release(self):
        if self.released: return
        self.released = True
        self.vao.release()
        self.element_position_buffer.release()
        self.element_uv_buffer.release()
        self.is_top_buffer.release()
        self.element_normal_buffer.release()
        self.coordinate_buffer.release()
        self.height_buffer.release()
        self.program.release()
