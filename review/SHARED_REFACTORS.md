# Shared Babbling Brook refactors — 2026-09-17

This revision implements the shared foundation discussed before Stratege.
`BillboardProgram.py`, `TileProgram.py`, the supplied map/game data, and all
artwork are byte-for-byte unchanged. No hue rotation or recolor masks were added.

## File loading and schemas

`codec/GameTablesCodec.py` owns named sections, escaped rows, table headers,
width validation, and typed dictionary rows. Unknown sections survive the generic
codec. `BabblingBrookFileCodec.py` defines the Babbling Brook schema and reports
unknown section names. Sections are matched by name, not position; sparse files
can overlay only the tables they change. Existing comment-prefixed column
headers and ordinary column headers are both accepted. Saves use canonical TSV;
whitespace/header formatting is normalized, while decoded values are preserved.

The old `GameFileCodec`, `PluginStringCodec`, and `GameStateCodec` import paths
remain available through compatibility aliases/imports. The old `GameRowCodec`
and `GameTableCodec` composition factories now live in the generic module.
The active game loader uses `BabblingBrookFileCodec` directly.

`GameFiles.load_content()` returns `(map_, plugin)` before application state
construction. `load()` composes that result with the injected `PluginOps.load()`.
Ordered overlays remain intact. Save instances replace the base instance tables,
so objects removed from either the map or `.game` data do not respawn on reload.

Inspection also found and fixed a missing `GameState` import that prevented the
original `GameFiles` module from importing, and a positional codec/header mismatch
that prevented reliable save round trips. The save test formerly depended on an
unshipped personal slot; it now creates its own fixture.

## Named animations

`CharacterArchetype.animations` is a dictionary keyed by animation name.
`PluginOps` loads and saves all names. Each animation keeps the existing two
frames in each of two directions and one positive frame duration. `standing` is
required and is the fallback for an unknown animation in `BillboardView`.

Texture preloading discovers all named animations. Existing standing, walking,
and running frames render as before. Attacking, disabled, cooldown, and custom
names are supported and tested; no new artwork or battle conditions were added.

## Map and motion

`Map` exposes `cell_center()`, `world_position()`, and
`is_continuous_transition()`. Membership supports integer cells and continuous
XY positions. The continuity query compares the two tiles' own heights at the
shared-edge midpoint, requires orthogonal adjacency, and uses a small numerical
tolerance. It does not infer continuity from whether erosion is enabled.

`MotionSegment` stores only start XY, end XY, quadratic height coefficients, and
duration. Its `__call__(time)` evaluates raw XYZ. The `linear_height()` and
`arc_height()` helpers return `(a, b, c)` for `a*t*t + b*t + c`. Arc maxima may be
at either endpoint; there is no separate free-fall representation.

`Motion` is a component containing segments, a segment index, and local elapsed
time. `MotionSystem.step(placements, motions, map_, seconds)` returns new
placement/motion dictionaries, consumes surplus time across segments, clamps
height to terrain, and removes completed motions. It raises for an evaluated
position outside the map. Motion paths must be authored within the map; this
system is not collision detection or pathfinding.

`TileMotionQuery(seconds_per_tile, maximum_height_change).segment(source,
destination, map_)` chooses linear motion over a continuous boundary, an arc
for a permitted discontinuity, or `None` when the discontinuous transition's
center-height difference exceeds the global limit. Smooth terrain oddities are
accepted and handled by terrain clamping. Occupancy/path rules remain external.

These utilities are available for Stratege. Babbling Brook continues to use its
existing movement and gravity systems. A future battle instance store should own
a `dict[EntityId, Motion]`; `MotionSystem` receives that dictionary directly.
Do not run gravity and scripted motion on the same entity. Motion serialization
and battle phases are not part of the Babbling Brook file schema.

## Visibility and highlights

`LineOfSightQuery(step_length).is_clear(source, target, placements, objects,
map_, disabled=(), excluded=())` ray-marches with a maximum sample spacing of
`step_length`. Choose a step much smaller than a tile. Each sample compares ray
height against terrain plus the tallest collidable billboard on the sample's
tile. Source/target positions include the intended sight/aim height. Pass their
entity IDs in `excluded`, and disabled unit IDs in `disabled`.

This uses the existing component dictionaries and `ObjectArchetype.height`;
there is no `SightOccluder`, unit enum dependency, or physics-driven attack rule.
Indirect attack rules will bypass this query in the battle layer.

`HighlightProgram.draw(coordinates, heights, colors, view)` takes parallel tile
coordinates, corner matrices, and RGBA colors. It follows the terrain's two
triangles, lifts them slightly, depth-tests, blends alpha, and does not write
depth. It remains an independent renderer and is not added to normal Babbling
Brook gameplay. Draw it after opaque terrain when a consumer needs highlights.

## Verification

- 38 tests passed with `BB_TEST_GL=1`, including a real EGL shader/render test.
- Supplied `.game` data decodes and round-trips semantically; section order,
  sparse overlays, escaping, duplicate rejection, and legacy headers are tested.
- Generated `.sav` snapshots restore inventory, placements, and animation state;
  removed objects stay removed and failed saves preserve the existing file.
- Named animation loading, persistence, fallback, and frame selection are tested.
- Map continuity, motion endpoints/maxima, variable durations, segment crossing,
  completion, clamping, and LOS blockers/exclusions are tested.
- Highlight checks cover blending, both triangles, depth preservation/occlusion,
  instance-buffer growth, and resource release.
- The actual game rendered two headless frames successfully using the supplied
  SVG textures. `smoke.png` is the inspected final frame.
- Python compilation passes. Interactive desktop play has not been exercised.

## Remaining work

The next work is Stratege's separate schema/state, units and conditions, geometric
`TileSelection`, range/path/occupancy rules, deployment and battle phases, and
integration of these motion/visibility/highlight utilities. The approved battle
phase order and per-player unlimited deployment turns remain as discussed.
Clothing palette variants belong in asset generation; the exact authoring
convention and battle artwork are still pending. No palette pipeline was added
in this revision.
