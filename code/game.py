"""Startup and save composition. Filesystem access stays at the application edge."""
from collections import defaultdict
from dataclasses import replace
import json
from math import isfinite
from pathlib import Path
import os

from pyglm import glm

from .codecs.GameFileCodec import GameFileCodec
from .codecs.IdentifierCodec import IdentifierCodec
from .codecs.maps.PpmImageCodec import PpmImageCodec
from .codecs.maps.MapCodec import MapCodec
from .codecs.maps.ObjectPlacementCodec import ObjectPlacementCodec
from .model.GameState import GameState
from .model.components.archetypes import (TileArchetype, ObjectArchetype,
    CharacterArchetype, CharacterAnimation, DirectionFrames)
from .model.components.instances import ObjectPlacement, VerticalPhysics, CharacterAnimationState
from .model.stores import ArchetypeComponentStores, InstanceComponentStores

identifier = IdentifierCodec()
codec = GameFileCodec()


def rows(sections, name, columns, required=False):
    if name not in sections:
        if required:
            raise ValueError(f"Missing section: {name}")
        return []
    table = sections[name]
    if table[0] != columns.split():
        raise ValueError(f"Invalid columns in {name}; expected {columns}")
    return table[1:]


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate identifier: {key!r}")
        result[key] = value
    return result


def boolean(value):
    if value not in ('true', 'false'):
        raise ValueError(f"Invalid boolean: {value!r}")
    return value == 'true'


def finite(value):
    result = float(value)
    if not isfinite(result):
        raise ValueError("Expected a finite number")
    return result


def read_sections(path):
    with open(path, encoding='utf-8') as file:
        result = codec.decode(file.read())
    if rows(result, 'format', 'key value', True) != [['version', '1']]:
        raise ValueError("Unsupported game format version")
    return result


def check_sections(sections, allowed):
    unknown = set(sections) - set(allowed.split())
    if unknown:
        raise ValueError(f"Unknown sections: {', '.join(sorted(unknown))}")


def definitions(sections):
    tiles = unique((identifier.decode(key), TileArchetype(texture, boolean(sides), float(erosion), boolean(solid)))
        for key, texture, sides, erosion, solid in rows(sections, 'tile_archetypes',
            'archetype texture show_exposed_sides max_erosion is_collidable', True))
    objects = {}
    for key, texture, static, solid, radius, height, width, gravity, action, label in rows(
            sections, 'object_archetypes',
            'archetype texture is_static is_collidable radius height width has_gravity action label', True):
        key = identifier.decode(key)
        if key in objects:
            raise ValueError(f"Duplicate archetype: {key}")
        value = ObjectArchetype(texture, boolean(static), boolean(solid), finite(radius),
            finite(height), finite(width), boolean(gravity), action, label)
        if not 0 < value.radius <= .5 or not 0 < value.width <= 1 or value.height <= 0:
            raise ValueError("Objects must have positive dimensions and fit one tile")
        objects[key] = value
    animations = {}
    for key, animation, direction, frame, texture, seconds in rows(sections,
            'character_animation_frames', 'archetype animation direction frame texture seconds_per_frame', True):
        key, direction, frame, seconds = identifier.decode(key), int(direction), int(frame), finite(seconds)
        if key not in objects or animation not in ('standing', 'walking', 'running') or direction not in (0, 1) or frame not in (0, 1) or seconds <= 0:
            raise ValueError("Invalid character animation frame")
        frames = animations.setdefault((key, animation), {})
        if (direction, frame) in frames:
            raise ValueError("Duplicate character animation frame")
        frames[direction, frame] = (texture, seconds)
    characters = {}
    for key in dict.fromkeys(key for key, _ in animations):
        decoded = {}
        for animation in ('standing', 'walking', 'running'):
            frames = animations.get((key, animation))
            if frames is None:
                continue
            if len(frames) != 4 or len({seconds for _, seconds in frames.values()}) != 1:
                raise ValueError("An animation requires two frames in each of two directions, with one frame duration")
            decoded[animation] = CharacterAnimation(tuple(DirectionFrames(tuple(frames[d, f][0] for f in (0, 1)))
                for d in (0, 1)), frames[0, 0][1])
        if 'standing' not in decoded:
            raise ValueError("A character requires standing frames")
        characters[key] = CharacterArchetype(**decoded)
    return ArchetypeComponentStores(objects, characters, tiles)


def placements(sections):
    return [ObjectPlacement(identifier.decode(entity), identifier.decode(archetype), glm.vec3(finite(x), finite(y), finite(z)))
        for entity, archetype, x, y, z in rows(sections, 'objects', 'entity archetype x y z')]


def instantiate(map_, archetypes, objects):
    positions, archetyped, physics, characters, static = {}, {}, {}, {}, {}
    seen = set()
    for placement in objects:
        entity, key, position = placement.entity, placement.archetype, placement.position
        if entity in seen:
            raise ValueError(f"Duplicate object: {entity!r}")
        seen.add(entity)
        if key not in archetypes.objects:
            raise ValueError(f"Unknown object archetype: {key!r}")
        if not all(isfinite(value) for value in position) or glm.vec2(position) not in map_:
            raise ValueError(f"Object outside map or invalid position: {entity!r}")
        definition = archetypes.objects[key]
        if definition.is_static and key not in archetypes.characters:
            static[entity] = placement
            continue
        positions[entity], archetyped[entity] = position, key
        if definition.has_gravity:
            ground = map_.height(glm.vec2(position))
            physics[entity] = VerticalPhysics(0.0, abs(position.z - ground) < 1e-5)
        if key in archetypes.characters:
            characters[entity] = CharacterAnimationState()
    if 'player' not in characters or 'player' not in physics:
        raise ValueError("A dynamic 'player' character with gravity is required")
    map_.static_objects = static
    return InstanceComponentStores(positions, archetyped, physics, characters)


def load_game(data: Path, save: Path | None = None):
    source = read_sections(data / 'world.game')
    check_sections(source, 'format tile_archetypes object_archetypes character_animation_frames tile_palette object_palette objects inventory globals')
    archetypes = definitions(source)
    tile_palette = unique((int(index), identifier.decode(key)) for index, key in rows(source, 'tile_palette', 'index archetype', True))
    with open(data / 'world.ppm', encoding='ascii') as file:
        image = PpmImageCodec().decode(file.read())
    map_ = MapCodec(tile_palette, archetypes.tiles).decode(image)
    if save is None:
        object_palette = unique((int(index), identifier.decode(key)) for index, key in rows(source, 'object_palette', 'index archetype', True))
        objects = ObjectPlacementCodec(object_palette, map_).decode(image) + placements(source)
        state = source
    else:
        state = read_sections(save)
        check_sections(state, 'format objects inventory globals physics character_states')
        rows(state, 'objects', 'entity archetype x y z', True)
        objects = placements(state)
    instances = instantiate(map_, archetypes, objects)
    inventory = defaultdict(int, unique((item, int(quantity)) for item, quantity in rows(state, 'inventory', 'item quantity')))
    if any(quantity < 0 for quantity in inventory.values()):
        raise ValueError("Inventory quantities cannot be negative")
    globals_ = unique((key, json.loads(value)) for key, value in rows(state, 'globals', 'key value'))
    if any(type(value) not in (type(None), bool, int, float, str) or isinstance(value, float) and not isfinite(value) for value in globals_.values()):
        raise ValueError("Globals must be finite scalar values")
    if save is not None:
        physics = unique((identifier.decode(entity), VerticalPhysics(finite(velocity), boolean(grounded)))
            for entity, velocity, grounded in rows(state, 'physics', 'entity vertical_velocity is_grounded', True))
        characters = unique((identifier.decode(entity), CharacterAnimationState(glm.vec2(finite(x), finite(y)), animation, finite(elapsed)))
            for entity, x, y, animation, elapsed in rows(state, 'character_states', 'entity facing_x facing_y animation elapsed', True))
        if physics.keys() != instances.physics.keys() or characters.keys() != instances.characters.keys():
            raise ValueError("Saved components do not match the object instances")
        if any(s.animation not in ('standing', 'walking', 'running') or s.elapsed < 0 for s in characters.values()):
            raise ValueError("Invalid saved animation state")
        instances = replace(instances, physics=physics, characters=characters)
    return GameState(map_, globals_, archetypes, instances, inventory)


def save_sections(model):
    objects = list(model.map.static_objects.values()) + [ObjectPlacement(entity, model.instances.archetyped[entity], position)
        for entity, position in model.instances.positionables.items()]
    return {
        'format': [['key', 'value'], ['version', '1']],
        'objects': [['entity', 'archetype', 'x', 'y', 'z'], *[
            [identifier.encode(p.entity), identifier.encode(p.archetype), *(repr(v) for v in p.position)] for p in objects]],
        'inventory': [['item', 'quantity'], *[[item, str(quantity)] for item, quantity in model.inventory.items()]],
        'globals': [['key', 'value'], *[[key, json.dumps(value, ensure_ascii=False, allow_nan=False)] for key, value in model.globals.items()]],
        'physics': [['entity', 'vertical_velocity', 'is_grounded'], *[
            [identifier.encode(entity), repr(p.vertical_velocity), str(p.is_grounded).lower()] for entity, p in model.instances.physics.items()]],
        'character_states': [['entity', 'facing_x', 'facing_y', 'animation', 'elapsed'], *[
            [identifier.encode(entity), repr(s.facing.x), repr(s.facing.y), s.animation, repr(s.elapsed)] for entity, s in model.instances.characters.items()]],
    }


def save_game(path: Path, model):
    text = codec.encode(save_sections(model))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    try:
        with open(temporary, 'w', encoding='utf-8', newline='\n') as file:
            file.write(text)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
