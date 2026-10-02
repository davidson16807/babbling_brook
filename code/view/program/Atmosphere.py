"""Shared surface-to-camera transfer for short, near-surface rays.

Distances are metres, Z is altitude, and density falls exponentially with
altitude as in LightQuery. Its light_color already includes source-to-surface
extinction; that incident illumination is treated as uniform along this short
ray. Rayleigh and Mie use LightQuery's phase functions. Additional scatterers
contribute only extinction, matching its two scattering phase weights.
"""

MAX_SCATTERERS = 4

ATMOSPHERE_SHADER = """
uniform vec3 camera_position;
uniform vec3 orthographic_direction;
uniform int scatterer_count;
uniform float scale_heights[4];
uniform vec3 scattering_coefficients[4];

// Integral of exp(-altitude / scale_height) along a straight segment.
float column_density(vec3 start, vec3 stop, float scale_height) {
    float start_height = max(start.z, 0.0);
    float stop_height = max(stop.z, 0.0);
    float delta = abs(stop_height - start_height) / scale_height;
    // Avoid cancellation for horizontal and nearly horizontal rays.
    float average = delta < 0.001
        ? 1.0 - delta * 0.5 + delta * delta / 6.0
        : (1.0 - exp(-delta)) / delta;
    return length(stop - start) * exp(-min(start_height, stop_height) / scale_height) * average;
}

vec3 optical_depth(vec3 start, vec3 stop) {
    vec3 depth = vec3(0.0);
    for (int j = 0; j < scatterer_count; ++j) {
        depth += scattering_coefficients[j] * column_density(start, stop, scale_heights[j]);
    }
    return depth;
}

vec3 atmospheric_color(vec3 surface_color, vec3 surface_position) {
    vec3 ray = surface_position - camera_position;
    // An orthographic pixel's origin lies on the camera plane, rather than
    // converging on the eye position. Perspective rays use the eye directly.
    if (dot(orthographic_direction, orthographic_direction) > 0.0) {
        vec3 direction = normalize(orthographic_direction);
        ray = direction * max(dot(ray, direction), 0.0);
    }
    vec3 ray_origin = surface_position - ray;
    float ray_length = length(ray);
    if (scatterer_count == 0 || ray_length <= 0.000001) return surface_color;
    // View direction points toward the surface, as in LightQuery.
    float cosine = clamp(dot(ray / ray_length, normalize(light_direction)), -1.0, 1.0);
    float rayleigh_phase = 3.0 * (1.0 + cosine * cosine) / (16.0 * 3.141592653589793);
    float g = 0.76;
    float mie_phase = (1.0 - g * g) /
        (4.0 * 3.141592653589793 * pow(1.0 + g * g - 2.0 * g * cosine, 1.5));

    vec3 in_scatter = vec3(0.0);
    float step_length = ray_length / 32.0;
    for (int i = 0; i < 32; ++i) {
        vec3 sample_position = ray_origin + ray * ((float(i) + 0.5) / 32.0);
        vec3 source = vec3(0.0);
        for (int j = 0; j < min(scatterer_count, 2); ++j) {
            float density = exp(-max(sample_position.z, 0.0) / scale_heights[j]);
            float phase = j == 0 ? rayleigh_phase : mie_phase;
            source += scattering_coefficients[j] * density * phase;
        }
        in_scatter += exp(-optical_depth(ray_origin, sample_position)) * source * step_length;
    }
    vec3 transmission = exp(-optical_depth(ray_origin, surface_position));
    return surface_color * transmission + light_color * in_scatter;
}
"""


def write_atmosphere(program, view):
    """Set every atmospheric uniform on each draw, including empty atmospheres."""
    if len(view.scatterers) > MAX_SCATTERERS:
        raise ValueError(f'At most {MAX_SCATTERERS} atmospheric scatterers are supported')
    if any(height <= 0 for height, _ in view.scatterers):
        raise ValueError('Atmospheric scale heights must be positive')
    padding = MAX_SCATTERERS - len(view.scatterers)
    program['camera_position'].value = tuple(view.camera_position)
    program['orthographic_direction'].value = (
        tuple(view.camera_forward) if view.camera_forward is not None else (0.0, 0.0, 0.0)
    )
    program['scatterer_count'].value = len(view.scatterers)
    program['scale_heights'].value = tuple(height for height, _ in view.scatterers) + (1.0,) * padding
    program['scattering_coefficients'].value = (
        tuple(tuple(coefficient) for _, coefficient in view.scatterers) + ((0.0, 0.0, 0.0),) * padding
    )
