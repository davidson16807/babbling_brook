#version 330 core
uniform sampler2D image;
in vec2 uv;
in float lighting;
out vec4 color;
void main() {
    color = vec4(texture(image, uv).rgb * lighting, 1.0);
}
