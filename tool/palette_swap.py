#!/usr/bin/env python3
"""Remap one PPM channel from the first palette to the second, in place."""
import argparse
from dataclasses import replace
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import stat
import sys
from tempfile import NamedTemporaryFile

# Import this checkout without requiring installation or starting the game.
ROOT = Path(__file__).resolve().parents[1]
if 'babbling_brook' not in sys.modules:
    spec = spec_from_file_location('babbling_brook', ROOT / 'code/__init__.py',
                                  submodule_search_locations=[str(ROOT / 'code')])
    package = module_from_spec(spec)
    sys.modules['babbling_brook'] = package
    spec.loader.exec_module(package)

from babbling_brook.codec.GameStateCodec import GameTableCodec
from babbling_brook.codec.PrimitiveListCodec import PrimitiveListCodec
from babbling_brook.codec.map.PpmImageCodec import PpmImageCodec


def read_palettes(text, channel):
    """Read two world.game-style TSV blocks, source first."""
    name = 'tile_palette' if channel == 1 else 'object_palette'
    blocks = re.split(r'\n[ \t]*\n', text.strip())
    if len(blocks) != 2:
        raise ValueError('Palette file must contain exactly two tables separated by a blank line')
    codec = GameTableCodec(f'# {name}\n# index\tarchetype',
                           PrimitiveListCodec(int), PrimitiveListCodec(str))
    palettes = []
    for number, block in enumerate(blocks, 1):
        lines = block.splitlines()
        if lines[0].strip() != f'# {name}':
            raise ValueError(f'Table {number} must start with # {name}')
        rows = [line for line in lines if line.strip() and not line.lstrip().startswith('#')]
        for row in rows:
            cells = row.split('\t')
            if len(cells) < 2 or any(cell.strip() for cell in cells[2:]):
                raise ValueError(f'Table {number} requires index and archetype columns (tab-separated)')
        palette = codec.decode(block)
        if not palette:
            raise ValueError(f'Table {number} is empty')
        if len(palette) != len(rows):
            raise ValueError(f'Table {number} contains duplicate indices')
        minimum = 1 if channel == 2 else 0
        if any(not minimum <= index <= 65535 or not entity.strip()
               for index, entity in palette.items()):
            raise ValueError(f'Table {number} requires indices {minimum}..65535 and nonempty archetypes')
        palettes.append(palette)
    return palettes


def remap(image, channel, source, destination):
    """Map original indices simultaneously; leave other channels untouched."""
    if channel not in (1, 2):
        raise ValueError('Channel must be 1 (tiles) or 2 (objects)')
    indices = {}
    for index, entity in destination.items():
        indices.setdefault(entity, index)  # First destination row wins for aliases.
    mapping = {0: 0} if channel == 2 else {}
    maximum = image.maximum
    for index in sorted({pixel[channel] for pixel in image.pixels} - mapping.keys()):
        if index not in source:
            raise ValueError(f'Image index {index} is missing from the first palette')
        entity = source[index]
        if entity not in indices:
            raise ValueError(f'Archetype {entity!r} (index {index}) is missing from the second palette')
        target = indices[entity]
        if not 0 <= target <= maximum:
            maximum = target
        mapping[index] = target
    return replace(image, 
        maximum = maximum,
        pixels=tuple(tuple(mapping[value] if component == channel else value
                        for component, value in enumerate(pixel))
                    for pixel in image.pixels)
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ppm', type=Path, help='Text P3 PPM to update in place')
    parser.add_argument('channel', type=int, choices=(1, 2), help='1 = tiles/green; 2 = objects/blue')
    parser.add_argument('palettes', type=Path, help='Two TSV palette tables: old first, new second')
    args = parser.parse_args(argv)
    temporary = None
    try:
        path = args.ppm.resolve()
        if path == args.palettes.resolve():
            raise ValueError('PPM and palette file must be different files')
        codec = PpmImageCodec()
        image = codec.decode(path.read_text(encoding='utf-8'))
        source, destination = read_palettes(args.palettes.read_text(encoding='utf-8-sig'), args.channel)
        result = remap(image, args.channel, source, destination)
        encoded = codec.encode(result)
        # Replace only after parsing, validation, and encoding all succeed.
        with NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                dir=path.parent, prefix=f'.{path.name}.', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
        temporary.chmod(stat.S_IMODE(path.stat().st_mode))
        temporary.replace(path)
    except (OSError, ValueError, IndexError) as error:
        parser.error(str(error))
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    changed = sum(a != b for a, b in zip(image.pixels, result.pixels))
    print(f'Remapped channel {args.channel}: {changed} pixels changed in {args.ppm}')


if __name__ == '__main__':
    main()
