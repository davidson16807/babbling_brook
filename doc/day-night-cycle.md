<!-- HUMAN WRITTEN -->

We should add a day/night cycle. 

The phase of the day/night cycle is stored in the .game file, under the cycles table, with the id "day". Its phase is a float in the range [0,1] where 0 and 1 is midnight and 0.5 is mid day. 

The phase of the day affects:
- the direction of the light source, which assumes a collimated light source of variable direction passed into the BillboardProgram or TileProgram
- the color of the light source, which is passed into the BillboardProgram or TileProgram
- the color of the background

During the day, the color of the light source and background is calculated at each timestep using function provided in truth.py. Light source color is calculated by a rgb_fraction_of_light_transmitted_through_atmosphere that's equivalent to G_calculation in truth.py. Background color is calculated by a rgb_fraction_of_distant_light_scattered_by_atmosphere that's equivalent to H_calculation in truth.py. You'll need to write some logic that wraps this function and provides its parameters. Most parameters can be calculated from the light source direction. Follow the example given here to calculate from the light source direction: https://www.shadertoy.com/view/NldGzn . You will have to adopt a representative values for the background color, since the background color is a constant, the real color of sky is dependent on the view direction, and the isometric engine will be able to look down into regions of atmosphere that would IRL occur below the ground, which the code I give you will poorly handle. I propose calculating background color by a representative view direction that's parallel to the ground and at a 90 degree angle to the sun.

The daytime light source direction is calculated as you might expect using glm.rotate with an angle of `2*pi*phase`. Assume for right now that the latitude is the equator so the sun sticks to the xz plane. 

 Calculate beta_sum from the sum of:

```
surface_air_rayleigh_scattering_coefficients  = glm.vec3(5.20e-6, 1.21e-5, 2.96e-5)
surface_air_mie_scattering_coefficients       = glm.vec3(2.1e-8,  2.1e-8,  2.1e-8 )
surface_air_absorption_coefficients           = glm.vec3(0)
```

During the night, the direction and color of the light and background will be given simple calculations based on the phase of the month, where 0 or 1 is a new moon and 0.5 is a full moon. The color of moon light is greyscale that is linear to `sin(pi*phase)` The direction of moon light is that of sunlight, but offset by an angle that is dependent on the phase of the moon, so during full moons the moon is opposite to the sun.

The logic for all this calculation will exist in a new LightQuery  class under model/query.

The day/night cycle is visible in both the game and the editor. The editor gives the user the ability to set a warp factor for the timestep using the <, >, and / keys. This warp factor is independent of the warp factors in the cycles table of the .game file. The < and > keys respectively slow down and speed up the timestep by factors that correspond to periods of cycles in the .game file. The / key will reset the warp factor to 1.