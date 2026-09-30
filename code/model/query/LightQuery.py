"""Sun/moon lighting and a representative horizontal sky ray.

Atmospheric distances are in scale heights; surface coefficients are per metre.
The column-density approximation is retained from the supplied Python code.
Ray geometry, scattering weights, and sky display conversion follow the shader.
Directions point from the scene towards the source, with world Z pointing up.
"""
from dataclasses import dataclass, field
from math import exp, pi, sin, sqrt

from pyglm import glm


@dataclass(frozen=True)
class Light:
    direction: glm.dvec3 = field(default_factory=lambda: glm.dvec3(-.5, -.7, 1))
    color: glm.dvec3 = field(default_factory=lambda: glm.dvec3(1))
    background: glm.dvec3 = field(default_factory=lambda: glm.dvec3(.16, .23, .25))

@dataclass(frozen=True)
class Scatterer:
    atmosphere_scale_height: float
    rgb_surface_air_scattering_coefficient: glm.dvec3

class LightQuery:

    def __init__(self, full_moon_color, sun_color):
        self.tiny = 1e-14
        self.huge = 1e14
        self.gamma = 2.2
        self.step_count = 32
        self.world_radius = 6_360_000.0
        self.scatterers = [
            Scatterer(8_000.0, glm.dvec3(5.20e-6, 1.21e-5, 2.96e-5)), #rayleigh
            Scatterer(1_200.0, glm.dvec3(1e-7)), #mie, use 1e-3 to 1.5e-3 for light to heavy rain
            Scatterer(1_200.0, glm.dvec3(1e-10, 1e-8, 3e-7)), # fire soot
            Scatterer(1_200.0, glm.dvec3(1e-10, 3e-9, 1e-8)), # dust storm
        ]
        self.atmosphere_height = 35_000
        self.sun_color = sun_color
        self.full_moon_color = full_moon_color
        self.exposure_intensity = 10.0  # W/m^2

    @staticmethod
    def direction(phase):
        return glm.dvec3(glm.rotate(glm.dmat4(1), 2*pi*(phase % 1), glm.dvec3(0, 1, 0))
                         * glm.dvec4(0, 0, -1, 0))

    def distances_along_3d_line_to_sphere(self, 
            A0 :glm.dvec3, A  :glm.dvec3, B0 :glm.dvec3, r  : float):
        t = glm.dot(B0 - A0, A);
        At = A0 + A*t - B0;
        y2 = r*r - glm.dot(At,At);
        dxr = glm.sqrt(max(y2, self.tiny));
        return glm.vec2(t - dxr, t + dxr) if y2 > 0. else None;

    @staticmethod
    def fraction_of_rayleigh_scattered_light_scattered_by_angle(
        cos_scatter_angle,
    ):
        return 3.0 * (1.0 + cos_scatter_angle**2) / (16.0 * pi)

    @staticmethod
    def fraction_of_mie_scattered_light_scattered_by_angle(
        cos_scatter_angle,
    ):
        g = 0.76
        return (1.0 - g*g) / (
            (4.0*pi) * (1.0 + g*g - 2.0*g*cos_scatter_angle)**1.5
        )

    '''
    "approx_air_column_density_ratio_through_atmosphere" 
      calculates the distance you would need to travel 
      along the surface to encounter the same number of particles in a column of arbitrary direction. 
    It does this by finding an integral using integration by substitution, 
      then tweaking that integral to prevent division by 0. 
    All distances are recorded in scale heights.
    "a" and "b" are distances along the ray from closest approach.
      The ray is fired in the positive direction.
      If there is no intersection with the world, 
      a and b are distances from the closest approach to the upper bound.
    "z2" is the closest distance from the ray to the center of the world, squared.
    "r0" is the radius of the world.
    '''
    def approx_air_column_density_ratio_through_atmosphere(self, a, b, z2, r0):
        '''
        GUIDE TO VARIABLE NAMES:
         "x*" distance along the ray from closest approach
         "z*" distance from the center of the world at closest approach
         "r*" distance ("radius") from the center of the world
         "*0" variable at reference point
         "*2" the square of a variable
         "ch" a nudge we give to prevent division by zero, analogous to the Chapman function
        '''
        if b == a: return 0.0
        z2 = max(0.0, z2)
        x0 = sqrt(max(r0*r0-z2, self.tiny))
        if a < x0 and -x0 < b and z2 < r0*r0: return self.huge
        z = sqrt(z2)
        sqrt_z = sqrt(z)
        ra, rb = sqrt(a*a+z2), sqrt(b*b+z2)
        k = .6
        sqrt_half_pi = sqrt(pi/2)
        ch0 = (1-1/(2*r0))*sqrt_half_pi*sqrt_z + k*x0
        cha = (1-1/(2*ra))*sqrt_half_pi*sqrt_z + k*abs(a)
        chb = (1-1/(2*rb))*sqrt_half_pi*sqrt_z + k*abs(b)
        # Equivalent to min(exp(r0-z), 1), without overflowing at zenith.
        s0 = exp(min(r0-z, 0)) / (x0/r0 + 1/ch0)
        sa = exp(r0-ra) / max(abs(a)/ra + 1/cha, .01)
        sb = exp(r0-rb) / max(abs(b)/rb + 1/chb, .01)
        sign = lambda x: 1 if x > 0 else -1 if x < 0 else 0
        return max(sign(b)*(s0-sb) - sign(a)*(s0-sa), 0)

    def rgb_fraction_of_light_transmitted_through_atmosphere(
        self, view_origin, view_direction, view_start_length, view_stop_length,
        world_position, world_radius, scatterer_multipliers
    ):
        F = 1.0
        for scatterer, multiplier in zip(self.scatterers, scatterer_multipliers):
            h = scatterer.atmosphere_scale_height
            r = world_radius / h
            beta = scatterer.rgb_surface_air_scattering_coefficient * multiplier * h
            V0 = (view_origin + view_direction * view_start_length - world_position) / h
            V1 = (view_origin + view_direction * view_stop_length - world_position) / h
            V = view_direction  # unit vector pointing to pixel being viewed
            v0 = glm.dot(V0, V)
            v1 = glm.dot(V1, V)
            zv2 = max(0.0, glm.dot(V0, V0) - v0*v0)
            sigma = self.approx_air_column_density_ratio_through_atmosphere(v0, v1, zv2, r)
            F *= glm.exp(-sigma * beta)
        return F

    '''
    For an excellent introduction to what we're try to do here, see Alan Zucconi: 
    https://www.alanzucconi.com/2017/10/10/atmospheric-scattering-3/
    We will be using most of the same terminology and variable names.
    GUIDE TO VARIABLE NAMES:
    Uppercase letters indicate vectors.
    Lowercase letters indicate scalars.
    Going for terseness because I tried longhand names and trust me, you can't read them.
    "*v*"    property of the view ray, the ray cast from the viewer to the object being viewed
    "*l*"    property of the light ray, the ray cast from the object to the light source
    "y*"     distance from the center of the world to the plane shared by view and light ray
    "z*"     distance from the center of the world to along the plane shared by the view and light ray 
    "r*"     a distance ("radius") from the center of the world
    "h*"     the atmospheric scale height, the distance at which air density reduces by a factor of e
    "*2"     the square of a variable
    "*0"     property at the start of the raymarch along the view
    "*1"     property at the end of the raymarch along the view
    "*i"     property during an iteration of the raymarch
    "d*"     the change in a property across iterations of the raymarch
    "beta*"  a scattering coefficient, the number of e-foldings in light intensity per unit distance
    "gamma*" a phase factor, the fraction of light that's scattered in a certain direction
    "sigma*" a column density ratio, the density of a column of air relative to surface density
    "F*"     fraction of source light that reaches the viewer due to scattering for each color channel
    "*_ray"  property of rayleigh scattering
    "*_mie"  property of mie scattering
    "*_abs"  property of absorption
    setup variable shorthands
    express all distances in scale heights 
    express all positions relative to world origin
    "beta_*" indicates the rest of the fractional loss.
    it is dependant on wavelength, and the density ratio, which is dependant on height
    So all together, the fraction of sunlight that scatters to a given angle is: beta(wavelength) * gamma(angle) * density_ratio(height)
    number of iterations within the raymarch
    '''
    def _rgb_fraction_of_distant_light_scattered_by_atmosphere(
            self, v0, v1, y2, zv2, l0, VL, r, beta_sum):
        dv = (v1-v0) / self.step_count
        if dv == 0: return glm.dvec3(0)
        if dv < 0: raise ValueError('The view-ray endpoint must follow its start')
        result = glm.dvec3(0)
        for i in range(self.step_count):
            vi = dv*i + v0
            li = VL*(vi-v0) + l0
            zl2 = max(0, vi*vi + zv2 - li*li)
            sigma = (self.approx_air_column_density_ratio_through_atmosphere(v0, vi, y2+zv2, r)
                     + self.approx_air_column_density_ratio_through_atmosphere(li, 3*r, y2+zl2, r))
            result += glm.exp(glm.dvec3(r-sqrt(vi*vi+y2+zv2))-beta_sum*sigma)*dv
        return result

    def rgb_fraction_of_distant_light_scattered_by_atmosphere(
        self, view_origin, view_direction, view_start_length, view_stop_length,
        world_position, world_radius,
        light_direction, scatterer_multipliers
    ):
        F = 0.0
        V = view_direction  # unit vector pointing to pixel being viewed
        L = light_direction  # unit vector pointing to light source
        VL = max(-1.0, min(1.0, glm.dot(V, L)))
        # "gammas" indicates the fraction of scattered sunlight that scatters to a given angle (indicated by its cosine, A.K.A. "VL").
        # It only accounts for a portion of the sunlight that's lost during the scatter, which is irrespective of wavelength or density
        gammas = [
            self.fraction_of_rayleigh_scattered_light_scattered_by_angle(VL),
            self.fraction_of_mie_scattered_light_scattered_by_angle(VL),
        ]
        beta_sum = sum(
            scatterer.atmosphere_scale_height * scatterer.rgb_surface_air_scattering_coefficient * multiplier
            for scatterer, multiplier in zip(self.scatterers, scatterer_multipliers)
        )
        beta_gamma = sum(
            scatterer.atmosphere_scale_height * scatterer.rgb_surface_air_scattering_coefficient * multiplier * gamma
            for scatterer, multiplier, gamma in zip(self.scatterers, scatterer_multipliers, gammas)
        )
        for scatterer in self.scatterers:
            h = scatterer.atmosphere_scale_height
            r = world_radius / h
            V0 = (view_origin + view_direction * view_start_length - world_position) / h
            V1 = (view_origin + view_direction * view_stop_length - world_position) / h
            v0 = glm.dot(V0, V)
            v1 = glm.dot(V1, V)
            # "beta_*" indicates the rest of the fractional loss.
            # it is dependant on wavelength, and the density ratio, which is dependant on height
            # So all together, the fraction of sunlight that scatters to a given angle is: beta(wavelength) * gamma(angle) * density_ratio(height)

            l0 = glm.dot(V0, L)
            # Only y2 + zv2 and y2 + zl2 enter the integral. Fold the
            # perpendicular-plane distance into zv2 to avoid a singular cross
            # product when view and light are parallel (or antiparallel).
            y2 = 0.0
            zv2 = max(0.0, glm.dot(V0, V0) - v0*v0)

            F += self._rgb_fraction_of_distant_light_scattered_by_atmosphere(v0, v1, y2, zv2, l0, VL, r, beta_sum) * beta_gamma
        return F

    @staticmethod
    def solar_rgb_intensity():
        """Port of the shader's blackbody RGB irradiance at one AU, in W/m^2."""
        temperature = 5772.0
        planck = 6.62607004e-34
        light_speed = 299792458.0
        boltzmann = 1.3806485279e-23
        stefan_boltzmann = 5.670373e-8
        solar_radius = 695.7e6
        astronomical_unit = 149597870700.0

        def fraction_below(wavelength):
            z = planck * light_speed / (boltzmann * wavelength * temperature)
            return 15 / pi**4 * sum(
                (z**3 + 3*z*z/n + 6*z/n**2 + 6/n**3) * exp(-n*z) / n
                for n in (1, 2)
            )

        bands = glm.dvec3(*(fraction_below(hi) - fraction_below(lo)
                            for lo, hi in ((600e-9, 700e-9),
                                           (500e-9, 600e-9),
                                           (400e-9, 500e-9))))
        return (stefan_boltzmann * temperature**4
                * (solar_radius / astronomical_unit)**2 * bands)

    def march_stop(self, origin, direction):
        # Positions and distances here are in metres.
        atmosphere_radius = (self.world_radius + self.atmosphere_height)
        intersections = self.distances_along_3d_line_to_sphere(origin, direction, glm.dvec3(0), atmosphere_radius)
        if intersections is None or intersections.y < 0:
            raise ValueError('View ray does not intersect the atmosphere ahead')
        return intersections.y

    def light_color(self, light_direction, max_color, scatterer_multipliers):
        """Gamma-encoded transmission along the ray toward the sun."""
        march_origin = glm.dvec3(0, 0, self.world_radius + 1.0)
        march_direction = glm.normalize(light_direction)
        march_stop = self.march_stop(march_origin, march_direction)
        transmitted = self.rgb_fraction_of_light_transmitted_through_atmosphere(
            march_origin, march_direction, 0.0, march_stop, 
            glm.dvec3(0), # world position
            self.world_radius, 
            scatterer_multipliers
        )
        return max_color * transmitted

    def background_color(self, light_direction, max_color, scatterer_multipliers):
        """Display RGB looking horizontally, 90 degrees from solar azimuth."""
        view_origin = glm.dvec3(0, 0, self.world_radius + 1.0)
        light_direction = glm.normalize(light_direction)
        horizontal = glm.normalize(glm.dvec3(-light_direction.y, light_direction.x, 0))
        # Azimuth is undefined at zenith/nadir; any horizontal ray suffices.
        view_direction = (glm.normalize(horizontal) 
                          if glm.length(horizontal) > self.tiny
                          else glm.dvec3(0, 1, 0))
        view_stop = self.march_stop(view_origin, view_direction)
        scattered = self.rgb_fraction_of_distant_light_scattered_by_atmosphere(
            view_origin, view_direction, 0.0, view_stop,
            glm.dvec3(0), self.world_radius, light_direction,
            scatterer_multipliers,
        )
        return max_color * scattered

    def mix_color(self, light1, light2):
        direction1, color1 = light1
        direction2, color2 = light2
        brightness1 = glm.length(color1)
        brightness2 = glm.length(color2)
        interpolant = glm.smoothstep(-0.2, 0.2, (brightness2 - brightness1) / (brightness2 + brightness1)) if brightness2 + brightness1 else 1.0
        return (
            direction1 if interpolant < 0.5 else direction2, 
            glm.mix(color1, color2, interpolant)
        )

    def query(self, cycles, precipitation_factor=1):
        day = cycles['day'].phase
        month = cycles['month'].phase % 1
        water_vapor_multiplier = precipitation_factor * 10**(4*sin(pi*(cycles['precipitation'].phase % 1)))
        print(water_vapor_multiplier)
        sun = self.direction(day)
        moon = self.direction(day + month)
        moon_color = self.full_moon_color * sin(pi*(month))
        sun_occlusion = glm.smoothstep(-0.1, 0.0, sun.z)
        moon_occlusion = glm.smoothstep(-0.1, 0.0, moon.z)
        scatterer_multipliers = (1, water_vapor_multiplier)
        direction, light_color = self.mix_color(
            (sun, self.light_color(sun, self.sun_color, scatterer_multipliers) * sun_occlusion),
            (moon, self.light_color(moon, moon_color, scatterer_multipliers) * moon_occlusion),
        )
        _, background_color = self.mix_color(
            (sun, self.background_color(sun, self.sun_color, scatterer_multipliers) * sun_occlusion),
            (moon, self.background_color(moon, moon_color, scatterer_multipliers) * moon_occlusion),
        )
        return Light(direction, glm.dvec3(light_color), glm.dvec3(background_color))
