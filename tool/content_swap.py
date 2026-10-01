#!/usr/bin/env python3
"""Remap selected PPM palette entities using one palette and an entity map."""
import argparse
from dataclasses import replace
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import stat
import sys
from tempfile import NamedTemporaryFile

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


def read_definition(text, channel):
    """Return an index->entity palette and source-entity->destination-entity map."""
    palette_name = 'tile_palette' if channel == 1 else 'object_palette'
    blocks = re.split(r'\n[ \t]*\n', text.strip())
    if len(blocks) != 2:
        raise ValueError('Definition file must contain a palette and one mapping table')

    palette_codec = GameTableCodec(
        f'# {palette_name}\n# index\tarchetype',
        PrimitiveListCodec(int), PrimitiveListCodec(str),
    )
    mapping_codec = GameTableCodec(
        '# remap\n# from\tto',
        PrimitiveListCodec(str), PrimitiveListCodec(str),
    )

    if blocks[0].splitlines()[0].strip() != f'# {palette_name}':
        raise ValueError(f'First table must start with # {palette_name}')
    if blocks[1].splitlines()[0].strip() != '# remap':
        raise ValueError('Second table must start with # remap')

    palette = palette_codec.decode(blocks[0])
    remappings = mapping_codec.decode(blocks[1])
    if not palette:
        raise ValueError('Palette table is empty')
    minimum = 1 if channel == 2 else 0
    if any(not minimum <= index <= 65535 or not entity.strip()
           for index, entity in palette.items()):
        raise ValueError('Palette requires valid indices and nonempty entities')
    if len(palette) != len({index for index in palette}):
        raise ValueError('Palette contains duplicate indices')
    if len(remappings) != len({source for source in remappings}):
        raise ValueError('Mapping table contains duplicate source entities')
    if any(not source.strip() or not destination.strip()
           for source, destination in remappings.items()):
        raise ValueError('Mapping table requires nonempty entities')
    return palette, remappings


def remap(image, channel, palette, remappings):
    if channel not in (1, 2):
        raise ValueError('Channel must be 1 (tiles) or 2 (objects)')
    entity_to_index = {}
    for index, entity in palette.items():
        if entity in entity_to_index:
            raise ValueError(f'Palette contains duplicate entity {entity!r}')
        entity_to_index[entity] = index

    index_mapping = {0: 0} if channel == 2 else {}
    for source_entity, destination_entity in remappings.items():
        if source_entity not in entity_to_index:
            raise ValueError(f'Source entity {source_entity!r} is missing from the palette')
        if destination_entity not in entity_to_index:
            raise ValueError(f'Destination entity {destination_entity!r} is missing from the palette')
        index_mapping[entity_to_index[source_entity]] = entity_to_index[destination_entity]

    return replace(image, pixels=tuple(
        tuple(index_mapping.get(value, value) if component == channel else value
              for component, value in enumerate(pixel))
        for pixel in image.pixels
    ))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ppm', type=Path, help='Text P3 PPM to update in place')
    parser.add_argument('channel', type=int, choices=(1, 2), help='1 = tiles/green; 2 = objects/blue')
    parser.add_argument('definition', type=Path,
                        help='One palette table followed by a # remap entity table')
    args = parser.parse_args(argv)
    temporary = None
    try:
        path = args.ppm.resolve()
        if path == args.definition.resolve():
            raise ValueError('PPM and definition file must be different files')
        codec = PpmImageCodec()
        image = codec.decode(path.read_text(encoding='utf-8'))
        palette, remappings = read_definition(
            args.definition.read_text(encoding='utf-8-sig'), args.channel)
        result = remap(image, args.channel, palette, remappings)
        encoded = codec.encode(result)
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
