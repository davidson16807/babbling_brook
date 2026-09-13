from functools import partial
import json
from types import SimpleNamespace

from pyglm import glm

from .ComposedCodec import ComposedCodec
from .ConcatenatedListCodec import ConcatenatedListCodec
from .ContainerListCodec import ContainerListCodec
from .DictionaryListCodec import DictionaryListCodec
from .DelimitedStringsCodec import DelimitedStringsCodec
from .EscapedTextCodec import EscapedTextCodec
from .MappedCodec import MappedCodec
from .ObjectListCodec import ObjectListCodec
from .PrimitiveListCodec import PrimitiveListCodec
from .CommentedStringCodec import CommentedStringCodec
from .PrefixedStringCodec import PrefixedStringCodec
from .ZippedCodec import ZippedCodec
from ..model.components.archetypes import TileArchetype, ObjectArchetype
from ..model.components.instances import VerticalPhysics, CharacterAnimationState


def _codec(encode, decode, item_count=1):
	return SimpleNamespace(encode=encode, decode=decode, item_count=item_count)


def _tuple_codec(*codecs):
	codec = ConcatenatedListCodec(*codecs)
	return _codec(codec.encode, lambda code: tuple(codec.decode(code)),
		sum(codec.item_count for codec in codecs))


def _vector_codec(Container, item_count):
	codec = ContainerListCodec(Container, float, item_count)
	# The supplied ContainerListCodec.decode references undefined names.
	# Keep that dependency unchanged and supply the vector conversion here.
	return _codec(codec.encode,
		lambda code: Container([float(value) for value in code[:item_count]]), item_count)


def _cell_codec(encode, decode):
	return _codec(lambda content: [encode(content)], lambda code: decode(code[0]))


boolean = _cell_codec(lambda value: str(value).lower(),
	lambda value: bool(('false', 'true').index(value)))
scalar = _cell_codec(partial(json.dumps, ensure_ascii=False, allow_nan=False), json.loads)


def GameRowCodec(key_codec, value_codec, column_delimiter='\t'):
	return ComposedCodec(
		ConcatenatedListCodec(key_codec, value_codec),
		MappedCodec(EscapedTextCodec()),
		DelimitedStringsCodec(column_delimiter),
	)


def GameTableCodec(header, key_codec, value_codec,
		column_delimiter='\t', row_delimiter='\n', comment_delimiter='#'):
	rows = DelimitedStringsCodec(row_delimiter)
	return ComposedCodec(
			DictionaryListCodec(),
			MappedCodec(GameRowCodec(key_codec, value_codec, column_delimiter=column_delimiter)),
			_codec(rows.encode, lambda code: rows.decode(code) if code else []),
			CommentedStringCodec(comment_delimiter),
			PrefixedStringCodec(header+row_delimiter),
			_codec(lambda code: code.rstrip(row_delimiter),
				lambda code: code.strip(row_delimiter)+row_delimiter),
		)


def GameTablesCodec(*table_codecs,
		column_delimiter='\t', row_delimiter='\n', table_delimiter='\n\n', comment_delimiter='#'):
	return ComposedCodec(
			ZippedCodec(*table_codecs),
			DelimitedStringsCodec(table_delimiter),
			_codec(lambda code: code, lambda code: code.strip(row_delimiter)),
		)


def GameStateCodec():
	position = ComposedCodec(
		_vector_codec(glm.vec3, 3), DelimitedStringsCodec(','), PrimitiveListCodec(str))
	return GameTablesCodec(
		GameTableCodec(
			'# format\n'+'\t'.join('key value'.split()),
			PrimitiveListCodec(str),
			PrimitiveListCodec(int),
		),
		GameTableCodec(
			'# globals\n'+'\t'.join('key value'.split()),
			PrimitiveListCodec(str),
			scalar,
		),
		GameTableCodec(
			'# inventory\n'+'\t'.join('item quantity'.split()),
			PrimitiveListCodec(str),
			PrimitiveListCodec(int),
		),
		GameTableCodec(
			'# tile_archetypes\n'+'\t'.join('archetype top_texture side_texture max_erosion is_collidable'.split()),
			PrimitiveListCodec(str),
			ObjectListCodec(TileArchetype,
				('top_texture', PrimitiveListCodec(str)),
				('side_texture', PrimitiveListCodec(str)),
				('max_erosion', PrimitiveListCodec(float)),
				('is_collidable', boolean),
			),
		),
		GameTableCodec(
			'# object_archetypes\n'+
			'\t'.join('archetype texture is_collidable radius height width has_gravity action label'.split()),
			PrimitiveListCodec(str),
			ObjectListCodec(ObjectArchetype,
				('texture', PrimitiveListCodec(str)),
				('is_collidable', boolean),
				('radius', PrimitiveListCodec(float)),
				('height', PrimitiveListCodec(float)),
				('width', PrimitiveListCodec(float)),
				('has_gravity', boolean),
				('action', PrimitiveListCodec(str)),
				('label', PrimitiveListCodec(str)),
			),
		),
		GameTableCodec(
			'# character_animation_frames\n'+'\t'.join('archetype animation direction frame texture seconds_per_frame'.split()),
			_tuple_codec(
				PrimitiveListCodec(str),
				PrimitiveListCodec(str),
				PrimitiveListCodec(int),
				PrimitiveListCodec(int),
			),
			_tuple_codec(PrimitiveListCodec(str), PrimitiveListCodec(float)),
		),
		GameTableCodec(
			'# tile_palette\n'+'\t'.join('index archetype'.split()),
			PrimitiveListCodec(int),
			PrimitiveListCodec(str),
		),
		GameTableCodec(
			'# object_palette\n'+'\t'.join('index archetype'.split()),
			PrimitiveListCodec(int),
			PrimitiveListCodec(str),
		),
		GameTableCodec(
			'# objects\n'+'\t'.join('entity archetype position'.split()),
			PrimitiveListCodec(str),
			_tuple_codec(PrimitiveListCodec(str), _codec(position.encode, position.decode)),
		),
		GameTableCodec('# physics\nentity\tvertical_velocity\tis_grounded', PrimitiveListCodec(str),
			ObjectListCodec(VerticalPhysics,
				('vertical_velocity', PrimitiveListCodec(float)),
				('is_grounded', boolean))),
		GameTableCodec('# character_states\nentity\tfacing_x\tfacing_y\tanimation\telapsed', PrimitiveListCodec(str),
			ObjectListCodec(CharacterAnimationState,
				('facing', _vector_codec(glm.vec2, 2)),
				('animation', PrimitiveListCodec(str)),
				('elapsed', PrimitiveListCodec(float)))),
	)
