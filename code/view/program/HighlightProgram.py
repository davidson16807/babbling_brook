"""Translucent tile-top highlights with no entity or game-rule dependencies."""
from struct import pack

import moderngl as gl


class HighlightProgram:
    ELEMENT_POSITIONS = ((0, 0), (1, 0), (1, 1), (0, 0), (1, 1), (0, 1))
    VERTEX_SHADER = """#version 330 core
uniform mat4 clip_from_world;
in ivec2 element_position;
in vec2 coordinate;
in mat2 heights;
in vec4 rgba;
out vec4 tint;
void main() {
    bool is_rotate = abs(heights[1][0] - heights[0][1])
                   > abs(heights[0][0] - heights[1][1]);
    ivec2 corner = is_rotate? 
        ivec2(1 - element_position.y, element_position.x) 
      : element_position;
    vec3 position = vec3(coordinate + vec2(corner), heights[corner.x][corner.y] + 0.01);
    gl_Position = clip_from_world * vec4(position, 1.0);
    tint = rgba;
}
"""
    FRAGMENT_SHADER = """#version 330 core
in vec4 tint;
out vec4 color;
void main() {
    color = tint;
}
"""

    def __init__(self, context):
        self.gl = context
        self.program = context.program(vertex_shader=self.VERTEX_SHADER, fragment_shader=self.FRAGMENT_SHADER)
        self.element_buffer = context.buffer(pack('12i', *(v for xy in self.ELEMENT_POSITIONS for v in xy)))
        self.coordinate_buffer = context.buffer(reserve=8)
        self.height_buffer = context.buffer(reserve=16)
        self.color_buffer = context.buffer(reserve=16)
        self.vao = context.vertex_array(self.program, [
            (self.element_buffer, '2i', 'element_position'),
            (self.coordinate_buffer, '2f /i', 'coordinate'),
            (self.height_buffer, '4f /i', 'heights'),
            (self.color_buffer, '4f /i', 'rgba'),
        ])
        self.released = False

    def draw(self, coordinates, heights, colors, view):
        """Parallel coordinate, corner-height matrix, and RGBA sequences.

        Draw after opaque terrain. The corner diagonal with the greatest height change is the triangle seam.
        depth-tests with a small lift, blends alpha, and does not write depth.
        """
        if self.released:
            return
        if not len(coordinates) == len(heights) == len(colors):
            raise ValueError("Highlight coordinates, heights, and colors must have equal lengths")
        if not coordinates:
            return
        data = (
            (self.coordinate_buffer, pack(f'{2 * len(coordinates)}f', *(v for xy in coordinates for v in xy))),
            (self.height_buffer, b''.join(h.to_bytes() for h in heights)),
            (self.color_buffer, pack(f'{4 * len(colors)}f', *(v for rgba in colors for v in rgba))),
        )
        for buffer, values in data:
            if buffer.size < len(values):
                buffer.orphan(len(values))
            buffer.write(values)
        self.program['clip_from_world'].write(view.clip_from_world.to_bytes())
        self.gl.enable_only(gl.DEPTH_TEST | gl.BLEND)
        self.gl.depth_func = '<='
        self.gl.blend_func = gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA
        old_depth_mask = self.gl.fbo.depth_mask
        self.gl.fbo.depth_mask = False
        try:
            self.vao.render(gl.TRIANGLES, vertices=6, instances=len(coordinates))
        finally:
            self.gl.fbo.depth_mask = old_depth_mask

    def release(self):
        if self.released:
            return
        self.released = True
        for resource in (self.vao, self.element_buffer, self.coordinate_buffer,
                         self.height_buffer, self.color_buffer, self.program):
            resource.release()
