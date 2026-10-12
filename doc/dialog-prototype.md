# Dialog prototype

Run `python dialog.py` from the extracted project after installing `.[render]`.
The installed entry point is `babbling-brook-dialog`; the module entry point is
`python -m babbling_brook.dialog`. Explorer and editor remain separate apps.

## Controls

- Drag inventory words to the sentence tray; clicking a word also adds it.
- New words open their inflection grid with the canonical form selected.
- Click a word in the sentence to reopen its forms. Click a form to select it;
  Escape or Close keeps the current selection and collapses the grid.
- Drag a phrase's outer frame to move the entire phrase. Drop before another
  phrase, or into empty tray space to append. Left/Right move the selected phrase.
- Drop `red` or `small` inside a common noun phrase. Drag individual words to
  arrange them, including before/after articles. Adjectives cannot stand alone.
  Clicking an adjective opens its own forms (one form for these English adjectives).
- Right-click an adjective to remove it; right-click another word or frame to
  remove that phrase. Delete/Backspace removes the selected phrase.
- Scroll over the inventory, forms, or sentence tray to scroll that area.
  Previous/Next and Up/Down also work. Clear empties the sentence.
- Speak or Enter submits the sentence. Close the window to quit.

Inflection order is shuffled separately for each lexeme when a session starts,
then stays stable for that session. `--seed 7` reproduces a shuffle. Duplicate
surface forms occupy one grid cell but retain every underlying interpretation.
The grid exposes only English word forms, with no grammatical codes or glosses.

## Prototype language scope

The small vocabulary comprises personal pronouns (`I` in the inventory), ball,
boy, girl, house, give, see, take, talk, walk, red, and small. Nouns have singular
and plural forms, article choices, and forms with `to`. Verbs are affirmative,
active, present-tense finite forms. This is a deliberately bounded prototype,
not a validator for arbitrary English.

Supported patterns include:

- `I walk` / `the boys walk` / `she walks to the house`
- `you talk to the boy`
- `I see the girl` / `we take a ball`
- `I give the red ball to the boy`

A well-formed supported sentence displays `Understood.` and sets
`DialogState.command` to a language-agnostic verb and argument representation.
Malformed or unsupported statements display `What?` and produce no command.
No movement, inventory, NPC behavior, or world execution is connected yet.

## Implementation

`DialogState`, `DialogUpdater`, and `DialogView` follow the existing MVU layout.
Dialog state owns sentence parts, selection, dragging, scrolling, shuffled choices,
and feedback. Updaters replace it without Pygame calls. The layout used for hit
checking is the same layout rendered as the supplied `UiBox` values.
`PygameMessageQueue` translates input; `PygameUiView.draw_boxes` rasterizes boxes;
`UiProgram` draws them. Rendering and collision shaders are unchanged.

`EnglishDialog` is imported through the existing `LanguagesLibrary` adapter.
It builds dictstore traversals, invokes `InflectionGeneration` with the supplied
`ListTreeLanguage`, and retains generated list trees in `DictLookup`. The two
supplied generation classes are unchanged. On submission it resolves ambiguous
forms for the supported argument patterns, checks subject/verb agreement, and
compares the player's word order with the upstream `Language.map` result.
English generation and syntax are not replaced by handwritten inflection rules.

`lib/languages/SOURCE.md` identifies the exact upstream commit and included
runtime subset. No flashcard generators run. Set `BB_LANGUAGES` or pass
`--languages` to use a full external checkout instead. The included snapshot is
intended for running this extracted project; a standalone wheel does not bundle
its external runtime directory.

## Verification

```sh
python -m unittest discover -s test -p 'test_dialog.py' -v
python dialog.py --headless --demo --seed 7 --frames 2 --screenshot dialog.png
```

The headless path needs EGL; normal desktop operation uses Pygame's OpenGL
context. The demo builds and submits `I give the red ball to the boy`, then leaves
its noun phrase selected for inspection. Screenshots use the actual UI renderer.

Validation on this revision: all 12 targeted dialog tests pass, and the actual
OpenGL renderer produced both the empty dialog and the submitted demo. Desktop
mouse operation has not been manually tested.
