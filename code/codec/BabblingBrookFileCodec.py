"""Babbling Brook's table schema. Generic file mechanics live in GameTablesCodec."""

from pyglm import glm

from .GameTablesCodec import GameTablesCodec, TypedGameTableCodec
from .ConcatenatedContainerCodec import ConcatenatedContainerCodec
from .ContainerListCodec import ContainerListCodec
from .ObjectListCodec import ObjectListCodec
from .PrimitiveListCodec import PrimitiveListCodec, BooleanListCodec
from ..model.plugin.Plugin import Plugin
from ..model.component.archetypes import TileArchetype, ObjectArchetype
from ..model.component.instances import ObjectPlacement, VerticalPhysics, CharacterAnimationState


class BabblingBrookFileCodec:
    def __init__(self):
        self.tables = GameTablesCodec()
        self.schema = (
            ('format', 'format', TypedGameTableCodec(
                ['key', 'value'],
                PrimitiveListCodec(str),
                PrimitiveListCodec(int))),
            ('globals', 'globals', TypedGameTableCodec(
                ['key', 'value'],
                PrimitiveListCodec(str),
                PrimitiveListCodec(float))),
            ('inventory', 'inventory', TypedGameTableCodec(
                ['item', 'quantity'],
                PrimitiveListCodec(str),
                PrimitiveListCodec(int))),
            ('tiles', 'tile_archetypes', TypedGameTableCodec(
                ['archetype', 'top_texture', 'side_texture', 'max_erosion', 'is_collidable'],
                PrimitiveListCodec(str),
                ObjectListCodec(TileArchetype, ('top_texture', PrimitiveListCodec(str)), ('side_texture', PrimitiveListCodec(str)), ('max_erosion', PrimitiveListCodec(float)), ('is_collidable', BooleanListCodec())))),
            ('objects', 'object_archetypes', TypedGameTableCodec(
                ['archetype', 'texture', 'is_collidable', 'radius', 'height', 'width', 'has_gravity', 'action', 'label'],
                PrimitiveListCodec(str),
                ObjectListCodec(ObjectArchetype, ('texture', PrimitiveListCodec(str)), ('is_collidable', BooleanListCodec()), ('radius', PrimitiveListCodec(float)), ('height', PrimitiveListCodec(float)), ('width', PrimitiveListCodec(float)), ('has_gravity', BooleanListCodec()), ('action', PrimitiveListCodec(str)), ('label', PrimitiveListCodec(str))))),
            ('animation_frames', 'character_animation_frames', TypedGameTableCodec(
                ['archetype', 'animation', 'direction', 'frame', 'texture', 'seconds_per_frame'],
                ConcatenatedContainerCodec(tuple, PrimitiveListCodec(str), PrimitiveListCodec(str), PrimitiveListCodec(int), PrimitiveListCodec(int)),
                ConcatenatedContainerCodec(tuple, PrimitiveListCodec(str), PrimitiveListCodec(float)))),
            ('tile_palette', 'tile_palette', TypedGameTableCodec(
                ['index', 'archetype'],
                PrimitiveListCodec(int),
                PrimitiveListCodec(str))),
            ('object_palette', 'object_palette', TypedGameTableCodec(
                ['index', 'archetype'],
                PrimitiveListCodec(int),
                PrimitiveListCodec(str))),
            ('placements', 'objects', TypedGameTableCodec(
                ['entity', 'archetype', 'x', 'y', 'z'],
                PrimitiveListCodec(str),
                ObjectListCodec(ObjectPlacement, ('archetype', PrimitiveListCodec(str)), ('position', ContainerListCodec(glm.vec3, float, 3))))),
            ('physics', 'physics', TypedGameTableCodec(
                ['entity', 'vertical_velocity', 'is_grounded'],
                PrimitiveListCodec(str),
                ObjectListCodec(VerticalPhysics, ('vertical_velocity', PrimitiveListCodec(float)), ('is_grounded', BooleanListCodec())))),
            ('characters', 'character_states', TypedGameTableCodec(
                ['entity', 'facing_x', 'facing_y', 'animation', 'elapsed'],
                PrimitiveListCodec(str),
                ObjectListCodec(CharacterAnimationState, ('facing', ContainerListCodec(glm.vec2, float, 2)), ('animation', PrimitiveListCodec(str)), ('elapsed', PrimitiveListCodec(float))))),
        )

    def encode(self, plugin):
        return self.tables.encode({
            name: codec.encode(getattr(plugin, field))
            for field, name, codec in self.schema
        })

    def decode(self, text):
        tables = self.tables.decode(text)
        unknown = tables.keys() - {name for _, name, _ in self.schema}
        if unknown:
            raise ValueError(f"Unknown Babbling Brook sections: {', '.join(sorted(unknown))}")
        values = {}
        for field, name, codec in self.schema:
            if name in tables:
                try:
                    values[field] = codec.decode(tables[name])
                except (ValueError, TypeError, IndexError) as error:
                    raise ValueError(f"Invalid {name}: {error}") from error
        plugin = Plugin(**values)
        if plugin.format and plugin.format != {'version': 1}:
            raise ValueError("Unsupported game format; expected version 1")
        return plugin


# Compatibility for callers using the former factory name.
PluginStringCodec = BabblingBrookFileCodec
