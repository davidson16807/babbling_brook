# HUMAN VETTED

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
from ..model.plugin.Plugin import Plugin
from ..model.component.archetypes import (TileArchetype, ObjectArchetype, CharacterArchetype,
                                         AnimalArchetype, Liquid, Waypoint)
from ..model.component.Cycle import Cycle
from ..model.component.Map import Map
from ..model.component.Landmark import Landmark
from ..model.component.Waterlevel import Waterlevel
from ..model.component.instances import ObjectPlacement, VerticalPhysics, CharacterAnimationState


class PluginListCodec:
    """Maps the ordered game-file tables to and from a ``Plugin``."""
    item_count = 1
    def encode(self, plugin):
        return plugin.to_tables()
    def decode(self, code):
        return Plugin.from_tables(code)

def _codec(encode, decode, item_count=1):
	return SimpleNamespace(encode=encode, decode=decode, item_count=item_count)


def _optional(type):
    """An empty cell represents an absent reference (including map ID zero)."""
    return _codec(lambda value: ['' if value is None else str(value)],
                  lambda code: None if code[0] == '' else type(code[0]))


def _defaulted(type, default):
    """Spreadsheet trait cells may omit a numeric value to use its default."""
    return _codec(lambda value: [str(value)],
                  lambda code: default if code[0] == '' else type(code[0]))

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

def PluginStringCodec(table_delimiter='\n\n', table_regex_delimiter=r'\n\t*\n'):
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
				'# cycles #UNUSED\n# id\tphase\tperiod',
				PrimitiveListCodec(str),
				ObjectListCodec(Cycle,
					('phase', PrimitiveListCodec(float)),
					('period', PrimitiveListCodec(float)),
				),
			),
			GameTableCodec(
				'# maps #UNUSED\n# id\tname\tfilename\tnorth_map_id\tsouth_map_id\teast_map_id\twest_map_id\tsummer_temperature\twinter_temperature',
				PrimitiveListCodec(int),
				ObjectListCodec(Map,
					('name', PrimitiveListCodec(str)),
					('filename', PrimitiveListCodec(str)),
					('north_map_id', _optional(int)),
					('south_map_id', _optional(int)),
					('east_map_id', _optional(int)),
					('west_map_id', _optional(int)),
					('summer_temperature', PrimitiveListCodec(float)),
					('winter_temperature', PrimitiveListCodec(float)),
				),
			),
			GameTableCodec(
				'# inventory\n #'+'\t'.join('character item quantity'.split()),
				ConcatenatedContainerCodec(tuple, PrimitiveListCodec(str), PrimitiveListCodec(str)),
				PrimitiveListCodec(int),
			),
			GameTableCodec(
				'# tile_archetypes\n #'+'\t'.join('archetype top_texture side_texture max_erosion is_collidable windswept waterswept disturbed'.split()),
				PrimitiveListCodec(str),
				ObjectListCodec(TileArchetype,
					('top_texture', PrimitiveListCodec(str)),
					('side_texture', PrimitiveListCodec(str)),
					('max_erosion', PrimitiveListCodec(float)),
					('is_collidable', BooleanListCodec()),
					('windswept', BooleanListCodec()),
					('waterswept', BooleanListCodec()),
					('disturbed', BooleanListCodec()),
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
				'# character_archetypes #UNUSED\n# id\tmale\tlifestage\tskin\thair\tbald_prone\tdwarf\tstrong\tfat\tattractive\thungry\tthirsty\twants\tloves\tharasses\tfollows\tavoids\tguards\twanders\trun_speed\tswim_speed\tclimb_speed\tcolorblind\tdeaf\tblind\tspeaks_native\tspeaks_foreign\tnumeracy\tliteracy\tplaces_known\tpeople_known\trespect_level\trespects_level\twealth_level\theals\tmends\tcooks\tsmiths\tcarpents\tmasons\tpicks_locks\tcontrols_weather\tanimal_friend\towes_player\tunescortable\tcriminal',
				PrimitiveListCodec(str),
				ObjectListCodec(CharacterArchetype,
					('male', BooleanListCodec()),
					('lifestage', _defaulted(int, 1)),
					('skin', _defaulted(int, 3)),
					('hair', _defaulted(int, 3)),
					('bald_prone', BooleanListCodec()),
					('dwarf', BooleanListCodec()),
					('strong', BooleanListCodec()),
					('fat', BooleanListCodec()),
					('attractive', BooleanListCodec()),
					('hungry', BooleanListCodec()),
					('thirsty', BooleanListCodec()),
					('wants', PrimitiveListCodec(str)),
					('loves', PrimitiveListCodec(str)),
					('harasses', PrimitiveListCodec(str)),
					('follows', PrimitiveListCodec(str)),
					('avoids', PrimitiveListCodec(str)),
					('guards', PrimitiveListCodec(str)),
					('wanders', BooleanListCodec()),
					('run_speed', _defaulted(float, 2.0)),
					('swim_speed', _defaulted(float, 0.0)),
					('climb_speed', _defaulted(float, 0.0)),
					('colorblind', BooleanListCodec()),
					('deaf', BooleanListCodec()),
					('blind', BooleanListCodec()),
					('speaks_native', BooleanListCodec()),
					('speaks_foreign', BooleanListCodec()),
					('numeracy', _defaulted(int, 1)),
					('literacy', _defaulted(int, 0)),
					('places_known', _defaulted(int, 0)),
					('people_known', _defaulted(int, 0)),
					('respect_level', _defaulted(int, 1)),
					('respects_level', _defaulted(int, 1)),
					('wealth_level', _defaulted(int, 1)),
					('heals', BooleanListCodec()),
					('mends', BooleanListCodec()),
					('cooks', BooleanListCodec()),
					('smiths', BooleanListCodec()),
					('carpents', BooleanListCodec()),
					('masons', BooleanListCodec()),
					('picks_locks', BooleanListCodec()),
					('controls_weather', BooleanListCodec()),
					('animal_friend', BooleanListCodec()),
					('owes_player', BooleanListCodec()),
					('unescortable', BooleanListCodec()),
					('criminal', BooleanListCodec()),
				),
			),
			GameTableCodec(
				'# animal_archetypes #UNUSED\n# id\trun_speed\tswim_speed\tclimb_speed\twarm_blooded\tcolorblind\tuv_vision\theat_vision\tnight_vision\tnocturnal\tforages\thunts_alone\tpack_hunts\teats_berries\teats_grass\teats_small_game\teats_big_game',
				PrimitiveListCodec(str),
				ObjectListCodec(AnimalArchetype,
					('run_speed', _defaulted(float, 0.0)),
					('swim_speed', _defaulted(float, 0.0)),
					('climb_speed', _defaulted(float, 0.0)),
					('warm_blooded', BooleanListCodec()),
					('colorblind', BooleanListCodec()),
					('uv_vision', BooleanListCodec()),
					('heat_vision', BooleanListCodec()),
					('forages', BooleanListCodec()),
					('hunts_alone', BooleanListCodec()),
					('pack_hunts', BooleanListCodec()),
					('eats_berries', BooleanListCodec()),
					('eats_grass', BooleanListCodec()),
					('eats_small_game', BooleanListCodec()),
					('eats_big_game', BooleanListCodec()),
				),
			),
			GameTableCodec(
				'# liquid_archetypes #UNUSED\n# id\ttop_texture1\ttop_texture2\tfreezing_temperature\tfrozen_texture\tviscosity\tunpassable',
				PrimitiveListCodec(str),
				ObjectListCodec(Liquid,
					('top_texture1', PrimitiveListCodec(str)),
					('top_texture2', PrimitiveListCodec(str)),
					('freezing_temperature', PrimitiveListCodec(float)),
					('frozen_texture', PrimitiveListCodec(str)),
					('viscosity', PrimitiveListCodec(float)),
					('unpassable', BooleanListCodec()),
				),
			),
			GameTableCodec(
				'# waypoints #UNUSED\n# id\tname\tin_game_texture\tin_editor_texture\tis_door',
				PrimitiveListCodec(str),
				ObjectListCodec(Waypoint,
					('name', PrimitiveListCodec(str)),
					('in_game_texture', PrimitiveListCodec(str)),
					('in_editor_texture', PrimitiveListCodec(str)),
					('is_door', BooleanListCodec()),
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
			GameTableCodec(
				'# landmarks #UNUSED\n# id\tmap_id\tlexeme\tby_radius\tat_point_x\tat_point_y\tat_point_z\ton_point_x\ton_point_y\ton_point_z\tin_point_x\tin_point_y\tin_point_z\tunder_point_x\tunder_point_y\tunder_point_z\twithin_point_x\twithin_point_y\twithin_point_z\tbefore_point_x\tbefore_point_y\tbefore_point_z\tagainst_point_x\tagainst_point_y\tagainst_point_z',
				PrimitiveListCodec(str),
				ObjectListCodec(Landmark,
					('map_id', PrimitiveListCodec(int)),
					('lexeme', PrimitiveListCodec(str)),
					('by_radius', PrimitiveListCodec(float)),
					('at_point', ContainerListCodec(glm.vec3, float, 3)),
					('on_point', ContainerListCodec(glm.vec3, float, 3)),
					('in_point', ContainerListCodec(glm.vec3, float, 3)),
					('under_point', ContainerListCodec(glm.vec3, float, 3)),
					('within_point', ContainerListCodec(glm.vec3, float, 3)),
					('before_point', ContainerListCodec(glm.vec3, float, 3)),
					('against_point', ContainerListCodec(glm.vec3, float, 3)),
				),
			),
			GameTableCodec(
				'# waterlevels #UNUSED\n# id\tmap_id\thigh_tide_liquid_level\tlow_tide_liquid_level\tliquid_id',
				PrimitiveListCodec(int),
				ObjectListCodec(Waterlevel,
					('map_id', PrimitiveListCodec(int)),
					('high_tide_liquid_level', PrimitiveListCodec(float)),
					('low_tide_liquid_level', PrimitiveListCodec(float)),
					('liquid_id', _optional(str)),
				),
			),
		),
		DelimitedStringsCodec(table_delimiter, table_regex_delimiter, postfixed=True),
	)
