# HUMAN VETTED

from struct import pack

import moderngl as gl

from .ViewState import ViewState
from ..Textures import Textures


"""
`TileProgram` renders a swarm of textured 3D tiles represented through primitives

There is no game logic or entity lookup here. Each draw establishes its own
required depth/blend state. release() is explicit resource lifecycle management.
"""

class TileProgram:
    VERTEX_SHADER = """#version 330 core
uniform mat4 clip_from_world;
in vec2 in_coordinate;
in float in_southwest;
in float in_southeast;
in float in_northwest;
in float in_northeast;
out vec2 uv;
out float lighting;

void main() {
    const float bottom_height = 0.0;
    vec3 corners[4] = vec3[4](
        vec3(in_coordinate, in_southwest),
        vec3(in_coordinate + vec2(1, 0), in_southeast),
        vec3(in_coordinate + vec2(0, 1), in_northwest),
        vec3(in_coordinate + vec2(1, 1), in_northeast)
    );
    vec2 texcoords[4] = vec2[4](vec2(0, 0), vec2(1, 0), vec2(0, 1), vec2(1, 1));
    int indices[6] = int[6](0, 1, 3, 0, 3, 2);
    int face = gl_VertexID / 6;
    int vertex = gl_VertexID % 6;

    if (face > 0) {
        // Outward-wound edges: west, east, south, north.
        int starts[4] = int[4](0, 3, 1, 2);
        int ends[4] = int[4](2, 1, 0, 3);
        int edge = face - 1;
        vec3 p = corners[starts[edge]];
        vec3 q = corners[ends[edge]];
        corners = vec3[4](
            vec3(p.xy, bottom_height), vec3(q.xy, bottom_height), p, q
        );
        indices = int[6](2, 1, 0, 2, 3, 1);
    }

    int triangle = (vertex / 3) * 3;
    vec3 a = corners[indices[triangle]];
    vec3 b = corners[indices[triangle + 1]];
    vec3 c = corners[indices[triangle + 2]];
    vec3 normal = cross(b - a, c - a);
    float magnitude = length(normal);
    // Match the former mesher's degenerate-triangle threshold.
    if (magnitude <= 1e-8) {
        gl_Position = clip_from_world * vec4(a, 1.0);
        lighting = 0.60;
    } else {
        gl_Position = clip_from_world * vec4(corners[indices[vertex]], 1.0);
        lighting = 0.60 + 0.40 * max(dot(normal / magnitude, normalize(vec3(-0.5, -0.7, 1.0))), 0.0);
    }
    uv = texcoords[indices[vertex]];
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
        self.textures = textures
        self.coordinate_buffer = gl.buffer(reserve=16)
        self.southwest_buffer = gl.buffer(reserve=16)
        self.southeast_buffer = gl.buffer(reserve=16)
        self.northwest_buffer = gl.buffer(reserve=16)
        self.northeast_buffer = gl.buffer(reserve=16)
        self.vao = gl.vertex_array(self.program, [
            (self.coordinate_buffer, "2f /i", "in_coordinate"),
            (self.southwest_buffer, "1f /i", "in_southwest"),
            (self.southeast_buffer, "1f /i", "in_southeast"),
            (self.northwest_buffer, "1f /i", "in_northwest"),
            (self.northeast_buffer, "1f /i", "in_northeast")])
        self.released = False

    def draw(self,
        texture: str,
        coordinates: tuple[tuple[int, int], ...],
        southwest: tuple[float, ...],
        southeast: tuple[float, ...],
        northwest: tuple[float, ...],
        northeast: tuple[float, ...],
        view: ViewState
    ) -> None:
        """Draw unit tiles from parallel per-tile collections.

        Each named corner supplies one height per tile; north is +y.
        Sides extend from their top edge to the shader's fixed bottom height.
        Top triangles share the southwest–northeast diagonal. Texture names are resolved
        through Textures, as for the other programs.
        """
        if self.released: return
        self.gl.enable_only(gl.DEPTH_TEST)
        self.gl.fbo.depth_mask = True
        self.gl.depth_func = "<="
        self.program["clip_from_world"].write(view.clip_from_world.to_bytes())
        self.program["image"].value = 0

        self.textures.get(texture).use(0)
        # Upload per-tile properties; gl_VertexID supplies the fixed topology.
        coordinate_data = pack(f"{2 * len(coordinates)}f", *(value for pair in coordinates for value in pair))
        if self.coordinate_buffer.size < len(coordinate_data):
            self.coordinate_buffer.orphan(len(coordinate_data))
        self.coordinate_buffer.write(coordinate_data)

        southwest_data = pack(f"{len(southwest)}f", *southwest)
        if self.southwest_buffer.size < len(southwest_data):
            self.southwest_buffer.orphan(len(southwest_data))
        self.southwest_buffer.write(southwest_data)

        southeast_data = pack(f"{len(southeast)}f", *southeast)
        if self.southeast_buffer.size < len(southeast_data):
            self.southeast_buffer.orphan(len(southeast_data))
        self.southeast_buffer.write(southeast_data)

        northwest_data = pack(f"{len(northwest)}f", *northwest)
        if self.northwest_buffer.size < len(northwest_data):
            self.northwest_buffer.orphan(len(northwest_data))
        self.northwest_buffer.write(northwest_data)

        northeast_data = pack(f"{len(northeast)}f", *northeast)
        if self.northeast_buffer.size < len(northeast_data):
            self.northeast_buffer.orphan(len(northeast_data))
        self.northeast_buffer.write(northeast_data)

        # Two top triangles and two for each side.
        self.vao.render(gl.TRIANGLES, vertices=30, instances=len(coordinates))

    def release(self):
        if self.released: return
        self.released = True
        self.vao.release()
        self.coordinate_buffer.release()
        self.southwest_buffer.release()
        self.southeast_buffer.release()
        self.northwest_buffer.release()
        self.northeast_buffer.release()
        self.program.release()
