# Babbling Brook

This revision adds the desktop MVP implementation to the supplied model and shader
foundation. It preserves the `code/` source layout and exposes the package as
`babbling_brook` to avoid Python's built-in `code` and `codecs` modules.

**Validation status:** the six codec tests and Python compilation pass. Gameplay,
Pygame event integration, and actual OpenGL rendering have not been executed in
the delivery environment: PyGLM, Pygame-CE, and ModernGL were unavailable and the
network did not permit installing them. This is an implementation for review,
not a claim of a playtested build. See `review/REVIEW.md` for exact changes and
remaining verification.

## Run

Requires Python 3.10+, an OpenGL 3.3-capable desktop, and the dependencies below.
From this extracted directory:

```sh
python -m pip install -e '.[render]'
python -m babbling_brook
```

The equivalent installed command is `babbling-brook`. Keep `data/` in the working
directory, or pass `--data /path/to/data`.

| Input | Action |
| --- | --- |
| WASD | Move relative to the camera |
| Shift | Run |
| Space | Jump when grounded |
| E | Interact with the closest eligible neighboring object |
| Tab | Show or hide inventory |
| Middle mouse drag | Rotate between four isometric azimuths |
| F5 | Save to `saves/slot.sav` |
| F9 | Load that slot |
| Escape | Quit |

The player starts beside an apple. Press E and Tab to exercise pickup and the
actual `defaultdict[str, int]` inventory. Grass rises to the northwest; the stone
platform to the east can be reached by jumping. Trees, crates, a stationary
villager, apples, and sticks demonstrate static objects, characters, collision,
and mapped actions. Texture artwork is deliberately a small geometric placeholder
set. Optional walking/running animations currently reuse the breathing frames at
faster playback rates.

To resume directly or use another slot:

```sh
python -m babbling_brook --load --save saves/slot.sav
```

Saves are manual; quitting does not automatically overwrite the slot. A failed
load leaves the running game intact and displays the error. Save/load catches
filesystem and invalid-data errors and reports them through `GameState.message`.

## Data and architecture

- `data/world.ppm` is unchanged from the attachment. R is height in half-units,
  G selects a tile palette entry, B selects an initial object palette entry
  (zero places nothing).
- `data/world.game` supplies archetypes, palettes, four frames per character
  animation (two directions, two frames each), and optional additional objects.
  Identifiers are JSON scalar cells: `"player"` is a string ID, `1` an integer ID.
- `Map` owns the tile `Field` instances. Runtime entity-indexed component
  dictionaries, including `ObjectPlacement`, stay in `InstanceComponentStores`.
  Systems receive the specific dictionaries they need, rather than entire stores.
- `GameStateCodec.decode` returns a `Plugin`. `PluginOps.update` overlays plugin
  tables in load order, and `PluginOps.load` combines the result with a decoded
  `Map` to create the runtime `GameState`.
- Erosion uses the supplied capped-minimum rule, including the current tile.
  Each tile top has exactly two triangles along the h00–h11 diagonal. Height
  queries interpolate those same triangles. Exposed sides extend to the fixed
  bottom elevation at zero; overlapping neighboring sides are depth-tested.
- `PygameMessageQueue` remains the event boundary. The loop consumes its internal
  messages and fixed 1/120-second ticks. Updaters map model/message to model;
  systems handle component collections. No Pygame polling is used in game logic.
- `GameView` composes `TileView`, `BillboardView`, and `PygameUiView`. Programs
  receive primitive sequences. Pygame font surfaces are rendered through the
  OpenGL `UiProgram`; characters remain upright cylindrical billboards.
- Saves are sectioned TSV and contain all current static/dynamic object
  placements, inventory, globals, physics, and character states. Loading a save
  reads only tiles from the PPM and obtains object instances only from the save.
  Archetype definitions still come from `world.game`. Unknown sections are
  reported instead of silently discarded. The generic `GameFileCodec` preserves
  unknown table sections when decoding.

For section framing, a `# name` line immediately after a blank line (or at the
start) begins a section. Other lines beginning with optional whitespace and `#`
are comments. Cell escapes are `\t`, `\n`, `\r`, and `\\`. Duplicate sections,
duplicate IDs, malformed row widths, and invalid required fields are errors.

This slice intentionally leaves language services, quests, NPC schedules,
holding/throwing, and inventory management beyond pickup outside its scope.
Collision is a simple horizontal cylinder test and ground-height query, with
axis-separated sliding. It does not implement rigid-body pushing or standing on
billboard objects. No renderer optimization beyond simple cached terrain geometry
and cached textures was added.

## Verify

```sh
python -m unittest discover -s tests -v
```

When dependencies are missing, the gameplay and rendering modules explicitly
skip; a run with skips is not evidence of a working desktop game. The suite covers
codec round trips, erosion, mesh/height agreement, movement, jump/landing,
collision, interaction, save restoration without PPM respawning, and failed-save
preservation. An opt-in test compiles the actual shaders and draws to an EGL
framebuffer:

```sh
BB_TEST_GL=1 python -m unittest discover -s tests -v
python -m babbling_brook --headless --frames 2 --screenshot smoke.png
```

EGL is only needed for these headless checks. Desktop play uses the context created
by Pygame. A desktop smoke command is:

```sh
python -m babbling_brook --frames 120 --screenshot desktop-smoke.png
```

The placeholder PNGs ship ready to load. To regenerate them, optionally install
Pillow and run `python tools/make_placeholder_textures.py`; Pillow is not a runtime
game dependency.
