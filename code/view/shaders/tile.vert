#version 330 core
uniform mat4 clip_from_world;
in vec3 in_position;
in vec3 in_normal;
in vec2 in_uv;
out vec2 uv;
out float lighting;
void main() {
    gl_Position = clip_from_world * vec4(in_position, 1.0);
    uv = in_uv;
    lighting = 0.60 + 0.40 * max(dot(normalize(in_normal), normalize(vec3(-0.5, -0.7, 1.0))), 0.0);
}
