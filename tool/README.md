# Palette remapping

From the project directory:

```sh
python tool/remap_palette.py data/map/world.ppm 1 palettes.txt
```

The three arguments are the PPM, channel index, and a file containing exactly two palette tables. The script updates the PPM **in place**. Channel `1` is green/tile indices; channel `2` is blue/object indices. Red heights and the unselected channel remain unchanged.

The palette file uses the same tab-separated rows as `world.game`, with the original palette first, the replacement palette second, and a blank line between them:

```text
# tile_palette
# index	archetype
0	rock
1	grass
2	stone

# tile_palette
# index	archetype
0	stone
1	rock
2	grass
```

The separators in that example are literal tabs. For objects, use `# object_palette` for both tables and pass channel `2`. Object index `0` is reserved for no object, stays `0`, and must not appear in either object palette.

The script uses `PpmImageCodec`, `GameTableCodec`, and `PrimitiveListCodec` from this checkout. Its imports require the project's normal PyGLM dependency; no rendering packages are needed.

Matching is by exact archetype name. Multiple old indices may name the same archetype; if multiple new indices name it, the first row in the second table wins. Swapped indices are mapped simultaneously, not repeatedly. Unused source entries need not have destination matches.

Unknown image indices, missing destination archetypes, duplicate indices, malformed tables, and destination values above the PPM's declared maximum are errors. The original file is replaced only after successful validation and encoding. Dimensions and maximum are retained; whitespace and comments are normalized by `PpmImageCodec`.
