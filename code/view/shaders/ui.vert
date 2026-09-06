#version 330 core
uniform vec2 viewport;
uniform vec4 rect;
in vec2 in_corner;
out vec2 uv;
void main() {
    vec2 pixel = rect.xy + in_corner * rect.zw;
    gl_Position = vec4(pixel.x / viewport.x * 2.0 - 1.0, 1.0 - pixel.y / viewport.y * 2.0, 0.0, 1.0);
    uv = vec2(in_corner.x, 1.0 - in_corner.y);
}
