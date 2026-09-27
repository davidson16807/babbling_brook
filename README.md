# Babbling Brook

## Level editor

With the render dependencies installed, run the new standalone entry point:

```sh
python editor.py data/map/world.ppm
```

The required argument is the P3 PPM file to edit. Palettes, object definitions,
and textures come from this checkout's `data/world.game` and top-level `texture/`,
even when the PPM is elsewhere or the command runs from another directory.

| Input | Editor action |
| --- | --- |
| WASD | Move one tile in the nearest camera-relative grid direction; hold to repeat |
| Shift+WASD | Extend or shrink a rectangular selection from its anchor |
| IJKL | Use the regular game's snapped camera controls |
| Middle mouse drag | Free camera rotation, with elevation bounded to 0–90° |
| `+` / `-` (also `=` and keypad plus/minus) | Zoom in / out in every mode |
| Wheel down / up, `<` / `>` (also comma / period) | Decrease / increase the selected mode; default is zoom out / in |
| T / Z / E | Select tile / height / object channel editing |
| Escape | Return to zoom mode (does not quit) |
| `0`–`9` | Set the selected channel to that literal value on every selected tile |
| Delete | Set the selected channel to zero |
| Ctrl+C / Ctrl+V | Copy selection / paste clipboard |
| Ctrl+Z | Undo the last PPM edit |
| Ctrl+Shift+Z or Ctrl+Y | Redo a PPM edit |
| Ctrl+S or F5 | Save to the PPM passed on the command line |
| Window close | Quit; close again to discard unsaved edits when prompted |

The cursor is always a list of tile coordinates. Amber marks its moving end;
cyan marks the rest of the selection. Releasing Shift retains the selection for
editing; the next movement without Shift selects a single tile. All edits apply
to every selected tile. Wheel modifiers no longer select a channel; square
brackets no longer edit. `EditorState.channel` is `None` for zoom or the PPM
channel index: height `0`, tile `1`, object `2`. Numbers and Delete do nothing
in zoom mode. Numbers assign a single literal digit, not multi-digit entry.
Palette steps skip undefined IDs and stop at the ends. Literal numeric input
preserves unassigned IDs in the PPM: unknown tiles use the existing missing-tile
artwork, and unknown objects are omitted from the preview and marked missing
in the status. The editor uses `ObjectPlacementCodec(..., disable_validation=True)`
to skip unknown object IDs and the image/map dimension check. The flag defaults
to `False`, so game callers still validate both conditions.
Object ID zero removes the object. Heights cannot go below zero. Zoom uses
an orthographic span bounded to 1–128 world units. The PPM maximum grows when needed,
up to the format's 65535 limit. Saving preserves sample values and dimensions,
using normalized P3 whitespace (comments are not retained).

The clipboard is a PPM rectangle stored on `EditorState`, with all three channels
copied in northwest-to-southeast row order. A multi-tile paste starts at the
yellow tile as its northwest corner, regardless of camera or selection direction;
parts outside the map are clipped. A one-tile clipboard repeats across the
selection. Paste replaces all channels in zoom mode or only the active channel
in an edit mode. Copying never changes the source map or history.

`AppHistoryTraversal` is ported from the supplied cdcraft implementation and
injected into `EditorUpdater`. It keeps up to 100 PPM undo snapshots in the model;
new edits clear redo, and no-op edits do not enter history. Undo/redo rebuild map
geometry and object placements. Camera, selection, mode, and clipboard are not
history snapshots and remain unchanged by traversal. Saves do not clear history;
undo/redo mark the image unsaved, as in the reference. The reference's view-only
and soft-traversal logic is intentionally omitted.

`EditorState`, `EditorUpdater`, and `EditorView` form a separate MVU application.
Editor-specific application modules live in `code/editor/`; regular-game
application modules live in `code/game/`. Shared model, update, and view
modules remain in their existing packages.
The original PPM samples remain authoritative; map erosion and object placements
are rebuilt after edits. Game-only `.game` placements, including the player,
are not part of the PPM editor. `CursorUpdater` handles list-based tile selection,
and the existing `HighlightProgram` draws that list on the terrain. Input polling
and file writes stay in the entry point, with no held-key cache in the model.

Editor checks (including save/load compatibility with the game):

```sh
python -m unittest discover -s test -v
BB_TEST_GL=1 python -m unittest discover -s test -v
```

This revision adds the desktop MVP implementation to the supplied model and shader
foundation. It preserves the `code/` source layout and exposes the package as
`babbling_brook` to avoid Python's built-in `code` and `codecs` modules.

**Editor validation:** all 30 tests pass with `BB_TEST_GL=1`, including OpenGL
rendering. A scripted 22-frame Pygame/OpenGL session covers zoom, selection,
mode changes, channel assignment, copy/paste, undo/redo, saving, and reload.
The history port also matches the supplied JavaScript across 300 model-only
operations. Interactive desktop play has not been manually tested.

## Run

Requires Python 3.10+, an OpenGL 3.3-capable desktop, and the dependencies below.
From this extracted directory:

```sh
python -m pip install -e '.[render]'
python -m babbling_brook
```

The top-level `babbling_brook.py` bootstraps the `code/` package, like `editor.py`,
so `python -m babbling_brook` also runs directly from the checkout once its
dependencies are available. `python babbling_brook.py` uses the same entry point.
The equivalent installed command is `babbling-brook`. Keep `data/` and its
sibling `texture/` in the working directory, or pass `--data /path/to/data`.
To layer mods over the base game, list the files in load order; arguments without
a `.game` or `.mod` extension are ignored:

```sh
python -m babbling_brook data/world.game mod/weather.mod
```

Use `--map /path/to/world.ppm` when the map is not `DATA/map/world.ppm`.

| Input | Action |
| --- | --- |
| WASD | Move relative to the camera |
| Shift | Run |
| Space | Jump when grounded |
| E | Interact with the closest eligible neighboring object |
| Tab | Show or hide inventory |
| Middle mouse drag | Rotate between four isometric azimuths |
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

## Data and architecture

- `data/map/world.ppm` is unchanged from the attachment. R is height in half-units,
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
- `GameView` and `EditorView` format their own UI content as immutable `UiPanel`
  and `UiText` values (text, styles, widths, padding, and anchors). Both inject the
  same `PygameUiView`, whose `draw(viewport, panels)` method handles font metrics,
  wrapping, layout, rasterization, and atlas caching without reading application
  state. Panels with the same anchor stack inward in order; bottom anchoring is
  resolved after wrapping. Another backend can consume the same values without
  separate game/editor adapters. `UiProgram` still receives textured rectangles;
  characters remain upright cylindrical billboards.
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

When dependencies are missing, the gameplay and rendering modules explicitly
skip; a run with skips is not evidence of a working desktop game. The suite covers
codec round trips, erosion, mesh/height agreement, movement, jump/landing,
collision, interaction, save restoration without PPM respawning, and failed-save
preservation. An opt-in test compiles the actual shaders and draws to an EGL
framebuffer:

```sh
BB_TEST_GL=1 python -m unittest discover -s test -v
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
