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
    # 0/1 are the two sloped top triangles; 2–5 are west/east/south/north.
    ELEMENT_FACES = (
        0, 0, 0, 1, 1, 1,
        2, 2, 2, 2, 2, 2,
        3, 3, 3, 3, 3, 3,
        4, 4, 4, 4, 4, 4,
        5, 5, 5, 5, 5, 5,
    )

    VERTEX_SHADER = """#version 330 core
uniform mat4 clip_from_world;
in ivec3 element_position;
in vec2 element_uv;
in int element_face;
in vec2 coordinate;
in mat2 heights;
out vec2 uv;
out float lighting;

void main() {
    float height = element_position.z == 0? 0.0 : 
        heights[element_position.x][element_position.y];
    vec3 position = vec3(coordinate + vec2(element_position.xy), height);

    vec3 southwest = vec3(0, 0, heights[0][0]);
    vec3 northwest = vec3(0, 1, heights[0][1]);
    vec3 southeast = vec3(1, 0, heights[1][0]);
    vec3 northeast = vec3(1, 1, heights[1][1]);
    vec3 normal;
    if (element_face == 0) {
        normal = cross(southeast - southwest, northeast - southwest);
    } else if (element_face == 1) {
        normal = cross(northeast - southwest, northwest - southwest);
    } else {
        vec3 side_normals[4] = vec3[4](
            vec3(-1, 0, 0), vec3(1, 0, 0),
            vec3(0, -1, 0), vec3(0, 1, 0)
        );
        normal = side_normals[element_face - 2];
    }

    gl_Position = clip_from_world * vec4(position, 1.0);
    lighting = 0.60 + 0.40 * max(dot(normalize(normal), normalize(vec3(-0.5, -0.7, 1.0))), 0.0);
    uv = element_uv;
}
"""

    FRAGMENT_SHADER = """#version 330 core
uniform sampler2D image;
in vec2 uv;
in float lighting;
out vec4 color;
void main() {
    color = vec4(texture(image, uv).rgb * lighting, 1.0);
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
        self.element_face_buffer = gl.buffer(pack(
            f"{len(self.ELEMENT_FACES)}i", *self.ELEMENT_FACES
        ))
        self.coordinate_buffer = gl.buffer(reserve=16)
        self.height_buffer = gl.buffer(reserve=16)
        self.vao = gl.vertex_array(self.program, [
            (self.element_position_buffer, "3i", "element_position"),
            (self.element_uv_buffer, "2f", "element_uv"),
            (self.element_face_buffer, "1i", "element_face"),
            (self.coordinate_buffer, "2f /i", "coordinate"),
            (self.height_buffer, "4f /i", "heights"),
        ])
        self.released = False

    def draw(self,
        texture: str,
        coordinates: tuple[tuple[int, int], ...],
        heights: tuple[glm.mat2, ...],
        view: ViewState
    ) -> None:
        """Draw unit tiles from parallel coordinate and height-matrix collections.

        Matrix columns are west/east and rows are south/north.
        Sides extend from their top edge to the shader's fixed bottom height.
        Top triangles share the southwest–northeast diagonal.
        """
        if self.released: return
        self.gl.enable_only(gl.DEPTH_TEST)
        self.gl.fbo.depth_mask = True
        self.gl.depth_func = "<="
        self.program["clip_from_world"].write(view.clip_from_world.to_bytes())
        self.program["image"].value = 0

        self.textures.get(texture).use(0)
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
        self.element_face_buffer.release()
        self.coordinate_buffer.release()
        self.height_buffer.release()
        self.program.release()
