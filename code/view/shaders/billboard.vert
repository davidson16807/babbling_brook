#version 330 core
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
