#version 330 core
uniform sampler2D image;
in vec2 uv;
out vec4 color;
void main() {
    color = texture(image, uv);
    if (color.a < 0.5) discard;
}
