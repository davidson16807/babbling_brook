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
uniform vec3 light_direction;
in ivec3 element_position;
in vec2 element_uv;
in ivec3 element_normal;
in vec2 coordinate;
in mat2 heights;
in float base_height;
out vec2 uv;
out float lighting;
flat out int is_top;
flat out int is_ns;

ivec2 corner_rotate(ivec2 corner, bool is_rotated) {
    return is_rotated ? ivec2(1 - corner.y, corner.x) : corner;
}

vec3 corner_point(ivec2 corner, bool is_rotated) {
    corner = corner_rotate(corner, is_rotated);
    return vec3(vec2(corner), heights[corner.x][corner.y]);
}

void main() {

    is_top = element_normal.z;
    is_ns = abs(element_normal.y);
    bool is_rotated = abs(heights[1][0] - heights[0][1])
                    > abs(heights[0][0] - heights[1][1]);
    ivec2 corner = is_top == 1? 
        corner_rotate(element_position.xy, is_rotated)
      : element_position.xy;
    float height = element_position.z == 0? 
        base_height
      : heights[corner.x][corner.y];
    vec3 position = vec3(coordinate + vec2(corner), height);

    vec3 normal = vec3(element_normal);
    if (is_top == 1) {
        vec3 A = corner_point(ivec2(0, 0), is_rotated);
        vec3 B = corner_point(ivec2(1, 1), is_rotated);
        vec3 C = corner_point(gl_VertexID < 3? ivec2(1, 0): ivec2(0,1), is_rotated);
        normal = cross(C - A, B - A);
        normal = normal.z < 0? -normal : normal;
    }

    gl_Position = clip_from_world * vec4(position, 1.0);
    lighting = 0.60 + 0.40 * max(dot(normalize(normal), normalize(light_direction)), 0.0);
    uv = is_top == 1 ? vec2(corner) : vec2(element_uv.x, height);
    if (is_top == 1 && dot(normal.xy, normal.xy) > 0.0) {
        // Texture +V points uphill; fit the rotated tile within [0, 1].
        vec2 uphill = -normal.xy / (abs(normal.x) + abs(normal.y));
        uv = mat2(uphill.y, uphill.x, -uphill.x, uphill.y) * (uv - 0.5) + 0.5;
    }

}
"""

    FRAGMENT_SHADER = """#version 330 core
uniform sampler2D top_image;
uniform vec3 light_color;
uniform sampler2D ns_image;
uniform sampler2D we_image;
in vec2 uv;
in float lighting;
flat in int is_top;
flat in int is_ns;
out vec4 color;
void main() {
    vec3 texture_color;
    if (is_top == 1) {
        texture_color = texture(top_image, uv).rgb;
    } else {
        vec2 side_uv = vec2(uv.x, fract(uv.y));
        texture_color = is_ns == 1 ? texture(ns_image, side_uv).rgb
                                  : texture(we_image, side_uv).rgb;
    }
    color = vec4(texture_color * lighting * light_color, 1.0);
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
        self.base_height_buffer = gl.buffer(reserve=4)
        self.vao = gl.vertex_array(self.program, [
            (self.element_position_buffer, "3i", "element_position"),
            (self.element_uv_buffer, "2f", "element_uv"),
            (self.element_normal_buffer, "3i", "element_normal"),
            (self.coordinate_buffer, "2f /i", "coordinate"),
            (self.height_buffer, "4f /i", "heights"),
            (self.base_height_buffer, "1f /i", "base_height"),
        ])
        self.released = False

    def draw(self,
        top_texture: str,
        ns_texture: str,
        we_texture: str,
        coordinates: tuple[tuple[int, int], ...],
        heights: tuple[glm.mat2, ...],
        base_heights: tuple[float, ...],
        view: ViewState
    ) -> None:
        """Draw one tile per coordinate, height matrix, and base height.

        Matrix columns are west/east and rows are south/north.
        Sides extend from their top edge to the tile's base height.
        Top triangles share the diagonal with the greater absolute height change;
        ties use southwest–northeast. Side geometry and texture orientation stay fixed.
        Sloped top textures point uphill independently on each triangle.
        North/south faces use ns_texture; west/east faces use we_texture.
        Side textures repeat once per world height unit, cropping partial units.
        """
        if self.released:
            return
        if len(coordinates) != len(heights) or len(heights) != len(base_heights):
            raise ValueError("Tile coordinates, heights, and base heights must have equal lengths")
        if not coordinates:
            return
        self.gl.enable_only(gl.DEPTH_TEST | gl.CULL_FACE)
        self.gl.front_face = "ccw"
        self.gl.cull_face = "back"
        self.gl.fbo.depth_mask = True
        self.gl.depth_func = "<="
        self.program["clip_from_world"].write(view.clip_from_world.to_bytes())
        self.program["light_direction"].value = tuple(view.light_direction)
        self.program["light_color"].value = tuple(view.light_color)
        self.program["top_image"].value = 0
        self.program["ns_image"].value = 1
        self.program["we_image"].value = 2

        self.textures.get(top_texture).use(0)
        self.textures.get(ns_texture).use(1)
        self.textures.get(we_texture).use(2)
        coordinate_data = pack(f"{2 * len(coordinates)}f", *(value for pair in coordinates for value in pair))
        if self.coordinate_buffer.size < len(coordinate_data):
            self.coordinate_buffer.orphan(len(coordinate_data))
        self.coordinate_buffer.write(coordinate_data)

        height_data = b"".join(height.to_bytes() for height in heights)
        if self.height_buffer.size < len(height_data):
            self.height_buffer.orphan(len(height_data))
        self.height_buffer.write(height_data)

        base_height_data = pack(f"{len(base_heights)}f", *base_heights)
        if self.base_height_buffer.size < len(base_height_data):
            self.base_height_buffer.orphan(len(base_height_data))
        self.base_height_buffer.write(base_height_data)

        # Two top triangles and two for each side.
        self.vao.render(gl.TRIANGLES, vertices=len(self.ELEMENT_POSITIONS), instances=len(coordinates))

    def release(self):
        if self.released: return
        self.released = True
        self.vao.release()
        self.element_position_buffer.release()
        self.element_uv_buffer.release()
        self.element_normal_buffer.release()
        self.coordinate_buffer.release()
        self.height_buffer.release()
        self.base_height_buffer.release()
        self.program.release()
