#version 330 core
uniform mat4 clip_from_world;
in vec2 in_coordinate;
in float in_southwest;
in float in_southeast;
in float in_northwest;
in float in_northeast;
in vec2 in_west_lower;
in vec2 in_east_lower;
in vec2 in_south_lower;
in vec2 in_north_lower;
in float in_exposed_sides;
out vec2 uv;
out float lighting;

void main() {
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
        vec2 lower[4] = vec2[4](in_west_lower, in_east_lower.yx, in_south_lower.yx, in_north_lower);
        int edge = face - 1;
        vec3 p = corners[starts[edge]];
        vec3 q = corners[ends[edge]];
        vec2 low = lower[edge];
        vec2 difference = vec2(p.z, q.z) - low;
        if (in_exposed_sides < 0.5 || (difference.x <= 0.0 && difference.y <= 0.0)) {
            q = p;
            low = vec2(p.z);
        } else if (difference.x < 0.0 || difference.y < 0.0) {
            // Clip crossing edges to the portion exposed above the neighbor.
            float t = difference.x / (difference.x - difference.y);
            vec3 crossing = mix(p, q, t);
            if (difference.x < 0.0) {
                p = crossing;
                low.x = crossing.z;
            } else {
                q = crossing;
                low.y = crossing.z;
            }
        }
        corners = vec3[4](vec3(p.xy, low.x), vec3(q.xy, low.y), p, q);
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
