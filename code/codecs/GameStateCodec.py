from types import SimpleNamespace

from pyglm import glm

from .ComposedCodec import ComposedCodec
from .ConcatenatedContainerCodec import ConcatenatedContainerCodec
from .ContainerListCodec import ContainerListCodec
from .DictionaryListCodec import DictionaryListCodec
from .DelimitedStringsCodec import DelimitedStringsCodec
from .EscapedTextCodec import EscapedTextCodec
from .MappedCodec import MappedCodec
from .ObjectListCodec import ObjectListCodec
from .PrimitiveListCodec import PrimitiveListCodec, BooleanListCodec
from .CommentedStringCodec import CommentedStringCodec
from .PrefixedStringCodec import PrefixedStringCodec
from .ZippedCodec import ZippedCodec
from ..model.GameState import GameState
from ..model.Plugin import Plugin
from ..model.components.archetypes import TileArchetype, ObjectArchetype
from ..model.components.instances import ObjectPlacement, VerticalPhysics, CharacterAnimationState


class PluginListCodec:
    """Maps the ordered game-file tables to and from a ``Plugin``."""
    item_count = 1
    def encode(self, plugin):
        return plugin.to_tables()
    def decode(self, code):
        return Plugin.from_tables(code)

def _codec(encode, decode, item_count=1):
	return SimpleNamespace(encode=encode, decode=decode, item_count=item_count)

def GameRowCodec(key_codec, value_codec, column_delimiter='\t'):
	return ComposedCodec(
		ConcatenatedContainerCodec(list, key_codec, value_codec),
		MappedCodec(EscapedTextCodec()),
		DelimitedStringsCodec(column_delimiter),
	)

def GameTableCodec(header, key_codec, value_codec,
		column_delimiter='\t', row_delimiter='\n', comment_delimiter='#'):
	return ComposedCodec(
			DictionaryListCodec(),
			MappedCodec(GameRowCodec(key_codec, value_codec, column_delimiter=column_delimiter)),
			DelimitedStringsCodec(row_delimiter),
			CommentedStringCodec(comment_delimiter),
			PrefixedStringCodec(header+row_delimiter),
			SimpleNamespace(
				encode=lambda code: code.rstrip(row_delimiter), 
				decode=lambda code: code.strip(row_delimiter)+row_delimiter, 
				item_count=1),
		)

def GameStateCodec(table_delimiter='\n\n'):
	return ComposedCodec(
		PluginListCodec(),
		ZippedCodec(
			GameTableCodec(
				'# format\n #'+'\t'.join('key value'.split()),
				PrimitiveListCodec(str),
				PrimitiveListCodec(int),
			),
			GameTableCodec(
				'# globals\n #'+'\t'.join('key value'.split()),
				PrimitiveListCodec(str),
				PrimitiveListCodec(float),
			),
			GameTableCodec(
				'# inventory\n #'+'\t'.join('item quantity'.split()),
				PrimitiveListCodec(str),
				PrimitiveListCodec(int),
			),
			GameTableCodec(
				'# tile_archetypes\n #'+'\t'.join('archetype top_texture side_texture max_erosion is_collidable'.split()),
				PrimitiveListCodec(str),
				ObjectListCodec(TileArchetype,
					('top_texture', PrimitiveListCodec(str)),
					('side_texture', PrimitiveListCodec(str)),
					('max_erosion', PrimitiveListCodec(float)),
					('is_collidable', BooleanListCodec()),
				),
			),
			GameTableCodec(
				'# object_archetypes\n'+
				'\t'.join('archetype texture is_collidable radius height width has_gravity action label'.split()),
				PrimitiveListCodec(str),
				ObjectListCodec(ObjectArchetype,
					('texture', PrimitiveListCodec(str)),
					('is_collidable', BooleanListCodec()),
					('radius', PrimitiveListCodec(float)),
					('height', PrimitiveListCodec(float)),
					('width', PrimitiveListCodec(float)),
					('has_gravity', BooleanListCodec()),
					('action', PrimitiveListCodec(str)),
					('label', PrimitiveListCodec(str)),
				),
			),
			GameTableCodec(
				'# character_animation_frames\n #'+'\t'.join('archetype animation direction frame texture seconds_per_frame'.split()),
				ConcatenatedContainerCodec(tuple,
					PrimitiveListCodec(str),
					PrimitiveListCodec(str),
					PrimitiveListCodec(int),
					PrimitiveListCodec(int),
				),
				ConcatenatedContainerCodec(tuple, PrimitiveListCodec(str), PrimitiveListCodec(float)),
			),
			GameTableCodec(
				'# tile_palette\n #'+'\t'.join('index archetype'.split()),
				PrimitiveListCodec(int),
				PrimitiveListCodec(str),
			),
			GameTableCodec(
				'# object_palette\n #'+'\t'.join('index archetype'.split()),
				PrimitiveListCodec(int),
				PrimitiveListCodec(str),
			),
			GameTableCodec(
				'# objects\n #'+'\t'.join('entity archetype x y z'.split()),
				PrimitiveListCodec(str),
				ObjectListCodec(ObjectPlacement,
					('archetype', PrimitiveListCodec(str)),
					('position', ContainerListCodec(glm.vec3, float, 3)),
				),
			),
			GameTableCodec('# physics\n #'+'\t'.join('entity vertical_velocity is_grounded'.split()), 
				PrimitiveListCodec(str),
				ObjectListCodec(VerticalPhysics,
					('vertical_velocity', PrimitiveListCodec(float)),
					('is_grounded', BooleanListCodec()))),
			GameTableCodec('# character_states\n #'+'\t'.join('entity facing_x facing_y animation elapsed'.split()), 
				PrimitiveListCodec(str),
				ObjectListCodec(CharacterAnimationState,
					('facing', ContainerListCodec(glm.vec2, float, 2)),
					('animation', PrimitiveListCodec(str)),
					('elapsed', PrimitiveListCodec(float)))),
		),
		DelimitedStringsCodec(table_delimiter, postfixed=True),
	)
