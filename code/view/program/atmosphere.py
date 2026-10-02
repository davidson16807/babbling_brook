"""LightQuery's scattering at constant (surface) density, i.e. Beer's law over
the camera distance. Metres (tiles); coefficients in e-foldings per metre."""
from pyglm import glm

ATMOSPHERE_GLSL = """
uniform mat4 world_from_clip;
uniform vec3 rayleigh_coefficient;
uniform vec3 mie_coefficient;

vec3 apply_atmosphere(vec3 rgb, vec3 world_position, vec3 light_direction, vec3 light_color) {
    vec4 clip = clip_from_world * vec4(world_position, 1.0);
    vec4 near = world_from_clip * vec4(clip.xy / clip.w, -1.0, 1.0);
    vec3 ray = world_position - near.xyz / near.w;
    float VL = dot(normalize(ray), normalize(light_direction));
    float g = 0.76, pi = 3.14159265;
    float gamma_ray = 3.0 * (1.0 + VL*VL) / (16.0*pi);
    float gamma_mie = (1.0 - g*g) / (4.0*pi * pow(1.0 + g*g - 2.0*g*VL, 1.5));
    vec3 beta = rayleigh_coefficient + mie_coefficient;
    vec3 transmitted = exp(-beta * length(ray));
    vec3 scattered = (rayleigh_coefficient*gamma_ray + mie_coefficient*gamma_mie)
                   / max(beta, vec3(1e-30)) * (1.0 - transmitted);
    return rgb * transmitted + light_color * scattered;
}
"""

def write_atmosphere_uniforms(program, view):
    program["world_from_clip"].write(glm.inverse(view.clip_from_world).to_bytes())
    program["rayleigh_coefficient"].value = tuple(view.rayleigh_coefficient)
    program["mie_coefficient"].value = tuple(view.mie_coefficient)
