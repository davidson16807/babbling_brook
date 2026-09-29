<!-- HUMAN WRITTEN -->

# Implementation

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

# Exploration of Cycle Length Designs

Cycle length is a matter of what cycle you want the users to concern themselves with. You want to time your cycle(s) to coincide with constraints in the real world. 

If you're starting out as a game dev, you really should build small games, so you should probably only **expect 5-40 real hours of play time**. That determines how many cycles the player will encounter. As for the length of each cycle, I recall a study that said **1.5 real hours is usually the amount of time a person can focus on a single task**. Movies tend to be that length because IRL you can plan ahead and block off that time, but if you're playing a game you'll have several play sessions and some might be interrupted, so a game might only require something less than that per session, like 1 hour. Whatever cycle of time you want the player to focus on, you want it to fit in that session. If you want the player to plan out what they're going to do over several cycles, you want that number of cycles to fit in a session. You also can't make the cycle too short, because if the player repeats an action every cycle, and a cycle is 6 minutes, they have to do that action every 6 minutes and it gets really repetitive.

If your game is like **Minecraft, Terraria, or Majora's Mask**, you want the player to plan out their actions several game days in advance, so 3 game days roughly fit in 1 real hour.

These games don't require you to sleep, and there are many days where you go without it. If your game is like **Bully**, you force the player to sleep, and if they don't then they simply pass out where they stand and wake up the next morning. This means that your intended play cycle is only half a game day. If you want the same number of play cycles in a session as Minecraft, you need double its game day length. That's exactly what we see: Bully's game day is twice that of Minecraft's.

In the case of **Majora's Mask**, you might plan out actions for several game days, but you want the player to squeeze in all their actions before the world ends, after which the cycle repeats and most player progress is lost, so the player can't plan out longer than that. You can fit 3 game days into a 1 real hour play session, so the developers made it so that the world ends in 3 days.

If your game is like **Dwarf Fortress**, the story is more about a fortress or civilization than a character. You want the player to squeeze in all their actions before the winter arrives, but situations come up so often that you can't plan ahead several game years, so the game year is ~1 real hour. The user largely doesn't care about the number of game days that pass, so the length of game day is whatever needed for there to be a reasonable number of those in a game year. There are 12 months in a year, so if you have a werebeast infestation you can expect to be attacked every 5 real minutes, which makes a werebeast infestation a fast paced event that can quickly get out of hand, exactly as intended. Werebeast infestations only occur on occasion to prevent game play from becoming repetitive.

In the case of **Elder Scrolls Online**, players work together and share the same game state, including time of day, so they can't skip to arbitrary times. The game is not mechanically dependent on time of day, but there should still be a day/night cycle to provide variety, and players can't always play at a certain time of day IRL, so the day can be long but it must be short enough that you can experience different times of day regardless of your time zone or whether you play in the mornings or evenings, so there are 4 game days in a real day.

# Establishing Cycle Lengths

1 	The shortest games of acceptable length take 10 hours to play. From recent personal memory: Crash Bandicoot, Fable, Carrion
2	On the suggestion given [here]([https://www.youtube.com/watch?v=5MgBikgcWnY]), it takes **20 hours to become "okay" at something**. 
3	Using a more reliable source than the one above, it takes 20 hours of flying a plane to be trusted to fly alone, and 40 hours to be trusted flying others
4	The player is playing the game because they want to learn a language. 
5	From 1-4, we should expect 10 hours of content for minimum viable product (MVP), not less than 20 hours upon minimum main quest (MMQ), and not more than 40 hours realistically.
6	Drilling inflection and vocabulary requires repetition, so much of this content could be made repetitive or procedural so long as there are minor variations to make the task of learning more pleasant.
7	Cycles of day, month, and year present a way to repeat and vary inflection, demonstrate concepts in language, and keeping things interesting: e.g. on different days with different party members, the user must command: "I sleep", "you sleep", or "we sleep", the user learns the word "month" by how things change across months
8	Cycles are ordered by their duration: day, weather, month, year
9 	Cycles should have mechanical consequences where possible to demonstrate the concept, justify the feature, and provide interesting variation despite repetition
10	From 9, the day/night cycle is enforced mechanically by nocturnal predators, special items (firebugs, luna moths) that can be collected for quests, changing access to certain locations (unable go out on moonless nights), and a tired status that resets upon sleeping
11 	From 9, the weather is implemented by several settings that oscillate in cycles with periods that are golden ratio powers of a day, and weather is enforced mechanically by changing access to certain locations (e.g. frozen lakes, swollen rivers), special items (frogs during rain, flowers after rain), and a cold status [after MMQ] 
12 	From 9, the month cycle consists of at least 2 days and is enforced mechanically by changing access to certain locations (going out on moonlit nights)
13 	From 9, the year cycle consists of at least 12 months and is enforced mechanically by changing access to certain locations (e.g. frozen lakes, swollen rivers) and variations on play (e.g. tower defense games in summer, snowball fights in winter)
14 	Games that feature mechanically enforced cycles (Minecraft, Terraria, Majora's Mask, etc.), especially cycles that affect enemy spawns, usually feature cycles with short periods, typically around 20 real minutes.
15	From 14, to simplify math, 1 game hour will be 1 real minute, and 1 game day will be 24 real minutes
16	From 4, the player is a child to justify why they are still learning the language, no more than 12 years old
17 	The player is old enough to have friends and play on their own, no less than 5 years old
18	The player is expected to remain a child throughout the game, otherwise the player asks questions about things that are not required to implement, like finding a girlfriend, job, wife, house, etc. [this might provide a way to extend game play past the main quest, but it should only be pursued well after MMQ]
19 	From 16-18, the main quest should be expected to take no more than 7 game years
20 	From 19 and 5, a game year is no less than 3 real hours or 9 game days, a season is no less than 45 real minutes or 2 game days, and a month is no less than 15 real minutes or less than a game day
21 	From 19 and 7, the main quest should be expected to take at least 2 years.
22 	From 20, 12, and 15, a game month must be no less than 2 game days or 48 real minutes
23 	From 22, 21, and 13, a game year at MMQ must be no less than 12 game months, 24 game days, 576 real minutes, or 9.6 real hours, and must be `12*M` game days where M is the number of days in a month. At MMQ, M must be exactly 2.
24 	From 23, a game season at MMQ is 6 game days, 144 real minutes, 2.4 real hours, and must be `3*M` days where M is the number of days in a month.
25	From 23, 21, 19, and 5, the main quest is expected to take no more than 2 game years, and any expansion to gameplay past that point will result in adding days to each month, M. [it might be nice to set M=3, so each day corresponds with nones, ides, and kalends, or M=4, so each day corresponds with phases of the moon].
26 	From 25, the expected main quest duration should be measured in terms of increments to M, where M≥2. 1 increment corresponds to roughly 10 real hours of expected game play. 
27 	From 24 and 14, seasons are intended to offer variation but the user cannot wait for them to unlock something that is critical to progress the game.
