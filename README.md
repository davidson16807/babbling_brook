# Babbling Brook

This revision adds the desktop MVP implementation to the supplied model and shader
foundation. It preserves the `code/` source layout and exposes the package as
`babbling_brook` to avoid Python's built-in `code` and `codecs` modules.

**Validation status:** editor model and persistence tests, Python compilation,
and offscreen OpenGL rendering pass. Interactive desktop playtesting has not
been performed in the delivery environment.

## Run

Requires Python 3.10+, an OpenGL 3.3-capable desktop, and the dependencies below.
From this extracted directory:

```sh
python -m pip install -e '.[render]'
python -m babbling_brook
```

The equivalent installed command is `babbling-brook`. Keep `data/` in the working
directory, or pass `--data /path/to/data`. To layer mods over the base game,
list the files in load order; arguments without a `.game` or `.mod` extension
are ignored:

```sh
python -m babbling_brook data/world.game mod/weather.mod
```

Use `--map /path/to/world.ppm` when the map is not `DATA/world.ppm`.

| Input | Action |
| --- | --- |
| WASD | Move relative to the camera |
| Shift | Run |
| Space | Jump when grounded |
| E | Interact with the closest eligible neighboring object |
| Tab | Show or hide inventory |
| Middle mouse drag | Rotate between four isometric azimuths |
| J / L | Rotate the camera by 90 degrees |
| I / K | Raise / lower the viewing angle by 30 degrees |
| F5 | Save to `save/slot.sav` |
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
python -m babbling_brook --load --save save/slot.sav
```

Saves are manual; quitting does not automatically overwrite the slot. A failed
load leaves the running game intact and displays the error. Save/load catches
filesystem and invalid-data errors and reports them through `GameState.message`.

## Level editor

The editor accepts exactly one positional argument: the P3 PPM to edit.

```sh
python -m babbling_brook.editor data/world.ppm
# Or, directly from this checkout:
python code/editor.py data/world.ppm
```

The installed command is `babbling-brook-editor data/world.ppm`.
The highlighted tiles are the cursor, and the camera follows its moving end. It can cross
objects and cliffs. WASD steps through the grid relative to the camera; holding
a key repeats after a short delay. Shift+WASD selects the rectangle between the
starting tile and the moving end, including both. Releasing Shift retains that
selection; the next move without Shift returns to one tile. Height and ID edits
apply to every selected tile as a single undoable change.

| Input | Editor action |
| --- | --- |
| WASD | Move the cursor by one tile |
| Shift+WASD | Extend or shrink the rectangular selection |
| J / L | Rotate the camera by 45 degrees |
| I / K | Raise / lower the viewing angle by 45 degrees |
| Middle mouse drag | Freely rotate and tilt the camera |
| Wheel up/down or period/comma (`>`/`<` keys) | Increase/decrease height by 0.5 |
| `[` / `]` | Select the previous/next defined tile ID |
| `(` / `)` | Select the previous/next defined object ID; 0 removes it |
| Ctrl+S or F5 | Save the PPM |
| Ctrl+Z / Ctrl+Y | Undo / redo (up to 100 edits) |
| Escape or close window | Close; repeat to discard unsaved edits |

The comma and period keys work with or without Shift. Wheel and `<`/`>` always
edit height. Parentheses are Shift+9 and Shift+0 on a US keyboard. Each selected
cell advances through its palette independently, stopping at the palette's ends.
Camera azimuth stays between 0 and 180 degrees; elevation stays between 0 and
90 degrees. Mouse look is continuous within these limits. Both input updaters
return angle deltas; the editor only limits their ranges, while the game snaps
its displayed azimuth to diagonal directions.

Palette definitions come from `world.game` beside the map, falling back to this
project's `data/world.game`. An optional `.game` with the same stem as the map is
then overlaid. Textures are resolved from the map's `texture/` folder with the
project's `data/texture/` as fallback. Objects authored only in `.game` files
are not PPM content and are not shown or edited here.

Saving writes the same dimensions and integer RGB samples as text P3. `Maxval`
is preserved unless an edit needs a larger value, up to 65,535; samples are never
rescaled. PPM comments and whitespace are rewritten. Terrain and object bases
are rebuilt after edits so erosion and placement heights stay consistent.

`EditorState`, `EditorUpdater`, and `EditorView` form a separate MVU path.
`EditorFiles` handles file access; the source PPM, decoded map, object placements,
cursor, camera, viewport, and status message belong to `EditorState`.

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
- `PluginStringCodec.decode` returns a `Plugin`. `PluginOps.update` overlays plugin
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
python -m unittest discover -s test -v
```

The tests cover cursor bounds, rectangular selections, camera controls, editing keys, erosion,
object heights, undo/redo, 16-bit PPM values, and saving without damaging the
original on failure. The wheel-adapter check skips if Pygame is unavailable.
The game can also render through EGL:

```sh
python -m babbling_brook --headless --frames 2 --screenshot smoke.png
```

EGL is only needed for these headless checks. Desktop play uses the context created
by Pygame. A desktop smoke command is:

```sh
python -m babbling_brook --frames 120 --screenshot desktop-smoke.png
```

The placeholder PNGs ship ready to load. To regenerate them, optionally install
Pillow and run `python tool/make_placeholder_textures.py`; Pillow is not a runtime
game dependency.
