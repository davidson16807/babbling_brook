# HUMAN VETTED

from pyglm import glm

from .ComposedCodec import ComposedCodec
from .ConcatenatedContainerCodec import ConcatenatedContainerCodec
from .ContainerListCodec import ContainerListCodec
from .DelimitedStringsCodec import DelimitedStringsCodec
from .EscapedTextCodec import EscapedTextCodec
from .MappedCodec import MappedCodec
from .ObjectListCodec import ObjectListCodec
from .PrimitiveListCodec import PrimitiveListCodec, BooleanListCodec
from .ZippedCodec import ZippedCodec
from .DictionaryListCodec import DictionaryListCodec
from .MultiKeyDictionaryListCodec import MultiKeyDictionaryListCodec
from .OptionalValueListCodec import OptionalValueListCodec
from .DefaultValueListCodec import DefaultValueListCodec
from .CommentedStringCodec import CommentedStringCodec
from .PrefixedStringCodec import PrefixedStringCodec
from .PaddedStringCodec import PaddedStringCodec
from .SetListCodec import SetListCodec
from ..model.plugin.Plugin import Plugin
from ..model.component.archetype import (TileArchetype, BoxArchetype, BillboardArchetype, CharacterArchetype,
                                        CreatureArchetype, Liquid, SeasonalTileArchetype,
                                        Waypoint, CardinalWaypoint)
from ..model.component.Cycle import Cycle
from ..model.component.zone import Biome, Zone, ZoneDirections, ZoneAdjacency, Waterlevel
from ..model.component.Landmark import Landmark
from ..model.component.instance import BillboardPlacement, BoxPlacement, VerticalPhysics, CharacterAnimationState


class PluginListCodec:
    """Maps the ordered game-file tables to and from a ``Plugin``."""
    item_count = 1
    def encode(self, plugin):
        return plugin.to_tables()
    def decode(self, code):
        return Plugin.from_tables(code)

def GameRowCodec(record_codec, column_delimiter='\t'):
	return ComposedCodec(
		record_codec,
		MappedCodec(EscapedTextCodec()),
		DelimitedStringsCodec(column_delimiter),
	)

def GameTableCodec(header, key_codec, value_codec,
		column_delimiter='\t', row_delimiter='\n', comment_delimiter='#'):
	"""A table whose rows are key cells followed by value cells, decoded as a dictionary."""
	return ComposedCodec(
			DictionaryListCodec(),
			GameRecordTableCodec(header, ConcatenatedContainerCodec(list, key_codec, value_codec),
				column_delimiter=column_delimiter, row_delimiter=row_delimiter,
				comment_delimiter=comment_delimiter),
		)

def GameRecordTableCodec(header, record_codec,
		column_delimiter='\t', row_delimiter='\n', comment_delimiter='#'):
	"""A table decoded as a list with one record per row."""
	return ComposedCodec(
			MappedCodec(GameRowCodec(record_codec, column_delimiter=column_delimiter)),
			DelimitedStringsCodec(row_delimiter),
			CommentedStringCodec(comment_delimiter),
			PrefixedStringCodec(header+row_delimiter),
			PaddedStringCodec(None, row_delimiter),
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
                '# globals #UNUSED\n #'+'\t'.join('key value'.split()),
                PrimitiveListCodec(str),
                PrimitiveListCodec(float),
            ),
            GameTableCodec(
                '# cycles\n# id\tphase\tperiod\twarp\twarp_until_phase',
                PrimitiveListCodec(str),
                ObjectListCodec(Cycle,
                    ('phase', PrimitiveListCodec(float)),
                    ('period', PrimitiveListCodec(float)),
                    ('warp', PrimitiveListCodec(float)),
                    ('warp_until_phase', PrimitiveListCodec(float)),
                ),
            ),
            GameTableCodec(
                '# biome\n# biome\tsummer_temperature\twinter_temperature\tleaf_state\tgrass_state\tis_snowy',
                PrimitiveListCodec(str),
                ObjectListCodec(Biome,
                    ('summer_temperature', PrimitiveListCodec(float)),
                    ('winter_temperature', PrimitiveListCodec(float)),
                    ('leaf_state', DefaultValueListCodec(int, 1)),
                    ('grass_state', DefaultValueListCodec(int, 1)),
                    ('is_snowy', BooleanListCodec()),
                ),
            ),
            ComposedCodec(
                SetListCodec(),
                GameRecordTableCodec(
                    '# biome spawns\n# biome\tcreature',
                    ConcatenatedContainerCodec(tuple, PrimitiveListCodec(str), PrimitiveListCodec(str)),
                ),
            ),
            GameTableCodec(
                '# zone\n# zone\tname\tmap_filename\tbiome',
                PrimitiveListCodec(str),
                ObjectListCodec(Zone,
                    ('name', PrimitiveListCodec(str)),
                    ('map_filename', PrimitiveListCodec(str)),
                    ('biome', PrimitiveListCodec(str)),
                ),
            ),
            GameTableCodec(
                '# zone water levels #UNUSED\n# zone\thigh_tide_liquid_level\tlow_tide_liquid_level\tliquid',
                PrimitiveListCodec(str),
                ObjectListCodec(Waterlevel,
                    ('high_tide_liquid_level', PrimitiveListCodec(float)),
                    ('low_tide_liquid_level', PrimitiveListCodec(float)),
                    ('liquid', OptionalValueListCodec(str)),
                ),
            ),
            GameTableCodec(
                '# zone directions\n# zone\tnorth\tsouth\teast\twest',
                PrimitiveListCodec(str),
                ObjectListCodec(ZoneDirections,
                    *((direction, OptionalValueListCodec(str)) for direction in ('north', 'south', 'east', 'west')),
                ),
            ),
            ComposedCodec(
                MultiKeyDictionaryListCodec(('zone1', 'colorcode'), ('zone2', 'colorcode')),
                GameRecordTableCodec(
                    '# zone adjacencies\n# zone1\tzone2\tcolorcode\tpreposition_to1\tpreposition_to2\tkey_to1\tkey_to2',
                    ObjectListCodec(ZoneAdjacency,
                        ('zone1', PrimitiveListCodec(str)),
                        ('zone2', PrimitiveListCodec(str)),
                        ('colorcode', PrimitiveListCodec(str)),
                        ('preposition_to1', PrimitiveListCodec(str)),
                        ('preposition_to2', PrimitiveListCodec(str)),
                        ('key_to1', OptionalValueListCodec(str)),
                        ('key_to2', OptionalValueListCodec(str)),
                    ),
                ),
            ),
            GameTableCodec(
                '# waypoints\n# archetype\tcolorcode\tdoor',
                PrimitiveListCodec(str),
                ObjectListCodec(Waypoint,
                    ('colorcode', PrimitiveListCodec(str)),
                    ('door', BooleanListCodec()),
                ),
            ),
            GameTableCodec(
                '# cardinal waypoints\n# archetype\tname\ttexture\tdirection\tcolorcode',
                PrimitiveListCodec(str),
                ObjectListCodec(CardinalWaypoint,
                    *((name, PrimitiveListCodec(str)) for name in ('name', 'texture', 'direction', 'colorcode')),
                ),
            ),
            GameTableCodec(
                '# landmarks #UNUSED\n# id\tmap\tlexeme\tby_radius\tat_position_x\tat_position_y\tat_position_z\ton_position_x\ton_position_y\ton_position_z\tin_position_x\tin_position_y\tin_position_z\tunder_position_x\tunder_position_y\tunder_position_z\twithin_position_x\twithin_position_y\twithin_position_z\tbefore_position_x\tbefore_position_y\tbefore_position_z\tagainst_position_x\tagainst_position_y\tagainst_position_z',
                PrimitiveListCodec(str),
                ObjectListCodec(Landmark,
                    ('map_id', PrimitiveListCodec(str)),
                    ('lexeme', PrimitiveListCodec(str)),
                    ('by_radius', PrimitiveListCodec(float)),
                    ('at_position', ContainerListCodec(glm.vec3, float, 3)),
                    ('on_position', ContainerListCodec(glm.vec3, float, 3)),
                    ('in_position', ContainerListCodec(glm.vec3, float, 3)),
                    ('under_position', ContainerListCodec(glm.vec3, float, 3)),
                    ('within_position', ContainerListCodec(glm.vec3, float, 3)),
                    ('before_position', ContainerListCodec(glm.vec3, float, 3)),
                    ('against_position', ContainerListCodec(glm.vec3, float, 3)),
                ),
            ),
            GameTableCodec('# colorcodes\n# colorcode\ttexture', PrimitiveListCodec(str), PrimitiveListCodec(str)),
            GameTableCodec(
                '# tile_archetypes\n #'+'\t'.join('archetype top_texture side_texture max_erosion has_detritus is_moist is_disturbed'.split()),
                PrimitiveListCodec(str),
                ObjectListCodec(TileArchetype,
                    ('top_texture', PrimitiveListCodec(str)),
                    ('side_texture', PrimitiveListCodec(str)),
                    ('max_erosion', PrimitiveListCodec(float)),
                    ('has_detritus', BooleanListCodec()),
                    ('is_moist', BooleanListCodec()),
                    ('is_disturbed', BooleanListCodec()),
                ),
            ),
            GameTableCodec(
                '# liquid_archetypes #UNUSED\n# archetype\ttop_texture1\ttop_texture2\tside_texture\tfreezing_temperature\tfrozen_texture\tviscosity\tis_unpassable',
                PrimitiveListCodec(str),
                ObjectListCodec(Liquid,
                    ('top_texture1', PrimitiveListCodec(str)),
                    ('top_texture2', PrimitiveListCodec(str)),
                    ('side_texture', PrimitiveListCodec(str)),
                    ('freezing_temperature', PrimitiveListCodec(float)),
                    ('frozen_texture', PrimitiveListCodec(str)),
                    ('viscosity', PrimitiveListCodec(float)),
                    ('is_unpassable', BooleanListCodec()),
                ),
            ),
            GameTableCodec(
                '# seasonal_tile_archetypes #UNUSED\n# id\tdefault\tfallen_leaves\tdead_grass\tsnowy',
                PrimitiveListCodec(str),
                ObjectListCodec(SeasonalTileArchetype,
                    ('default', PrimitiveListCodec(str)),
                    ('fallen_leaves', PrimitiveListCodec(str)),
                    ('dead_grass', PrimitiveListCodec(str)),
                    ('snowy', PrimitiveListCodec(str)),
                ),
            ),
            GameTableCodec(
                '# billboard_archetypes\n'+
                '\t'.join('archetype texture is_collidable radius height width has_gravity action lexeme'.split()),
                PrimitiveListCodec(str),
                ObjectListCodec(BillboardArchetype,
                    ('texture', PrimitiveListCodec(str)),
                    ('is_collidable', BooleanListCodec()),
                    ('radius', PrimitiveListCodec(float)),
                    ('height', PrimitiveListCodec(float)),
                    ('width', PrimitiveListCodec(float)),
                    ('has_gravity', BooleanListCodec()),
                    ('action', PrimitiveListCodec(str)),
                    ('lexeme', PrimitiveListCodec(str)),
                ),
            ),
            GameTableCodec(
                '# box_archetypes\n# archetype\ttop_texture\tside_texture\tscale_x\tscale_y\tscale_z\tis_collidable',
                PrimitiveListCodec(str),
                ObjectListCodec(BoxArchetype,
                    ('top_texture', PrimitiveListCodec(str)),
                    ('side_texture', PrimitiveListCodec(str)),
                    ('scale', ContainerListCodec(glm.vec3, float, 3)),
                    ('is_collidable', BooleanListCodec()),
                ),
            ),
            GameTableCodec(
                '# seasonal_billboard_archetypes #UNUSED\n# archetype\tleaf_state\ttexture',
                ConcatenatedContainerCodec(tuple, PrimitiveListCodec(str), PrimitiveListCodec(int)),
                PrimitiveListCodec(str),
            ),
            GameTableCodec(
                '# character_archetypes #UNUSED\n# archetype\tmale\tlifestage\tskin\thair\tbald_prone\tdwarf\tstrong\tfat\tattractive\thungry\tthirsty\twants\tloves\tharasses\tfollows\tavoids\tguards\twanders\trun_speed\tswim_speed\tclimb_speed\tcolorblind\tdeaf\tblind\tspeaks_native\tspeaks_foreign\tnumeracy\tliteracy\tplaces_known\tpeople_known\trespect_level\trespects_level\twealth_level\theals\tmends\tcooks\tsmiths\tcarpents\tmasons\tpicks_locks\tcontrols_weather\tcreature_friend\towes_player\tunescortable\tcriminal',
                PrimitiveListCodec(str),
                ObjectListCodec(CharacterArchetype,
                    ('male', BooleanListCodec()),
                    ('lifestage', DefaultValueListCodec(int, 1)),
                    ('skin', DefaultValueListCodec(int, 3)),
                    ('hair', DefaultValueListCodec(int, 3)),
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
                    ('run_speed', DefaultValueListCodec(float, 2.0)),
                    ('swim_speed', DefaultValueListCodec(float, 0.0)),
                    ('climb_speed', DefaultValueListCodec(float, 0.0)),
                    ('colorblind', BooleanListCodec()),
                    ('deaf', BooleanListCodec()),
                    ('blind', BooleanListCodec()),
                    ('speaks_native', BooleanListCodec()),
                    ('speaks_foreign', BooleanListCodec()),
                    ('numeracy', DefaultValueListCodec(int, 1)),
                    ('literacy', DefaultValueListCodec(int, 0)),
                    ('places_known', DefaultValueListCodec(int, 0)),
                    ('people_known', DefaultValueListCodec(int, 0)),
                    ('respect_level', DefaultValueListCodec(int, 1)),
                    ('respects_level', DefaultValueListCodec(int, 1)),
                    ('wealth_level', DefaultValueListCodec(int, 1)),
                    ('heals', BooleanListCodec()),
                    ('mends', BooleanListCodec()),
                    ('cooks', BooleanListCodec()),
                    ('smiths', BooleanListCodec()),
                    ('carpents', BooleanListCodec()),
                    ('masons', BooleanListCodec()),
                    ('picks_locks', BooleanListCodec()),
                    ('controls_weather', BooleanListCodec()),
                    ('creature_friend', BooleanListCodec()),
                    ('owes_player', BooleanListCodec()),
                    ('unescortable', BooleanListCodec()),
                    ('criminal', BooleanListCodec()),
                ),
            ),
            GameTableCodec(
                '# creature_archetypes #UNUSED\n# archetype\trun_speed\tswim_speed\tclimb_speed\tfly_speed\twarm_blooded\tcolorblind\tuv_vision\theat_vision\tforages\thunts_alone\tpack_hunts\teats_berries\teats_seeds\teats_grass\teats_fish\teats_small_game\teats_big_game',
                PrimitiveListCodec(str),
                ObjectListCodec(CreatureArchetype,
                    ('run_speed', DefaultValueListCodec(float, 0.0)),
                    ('swim_speed', DefaultValueListCodec(float, 0.0)),
                    ('climb_speed', DefaultValueListCodec(float, 0.0)),
                    ('fly_speed', DefaultValueListCodec(float, 0.0)),
                    ('warm_blooded', BooleanListCodec()),
                    ('colorblind', BooleanListCodec()),
                    ('uv_vision', BooleanListCodec()),
                    ('heat_vision', BooleanListCodec()),
                    ('forages', BooleanListCodec()),
                    ('hunts_alone', BooleanListCodec()),
                    ('pack_hunts', BooleanListCodec()),
                    ('eats_berries', BooleanListCodec()),
                    ('eats_seeds', BooleanListCodec()),
                    ('eats_grass', BooleanListCodec()),
                    ('eats_fish', BooleanListCodec()),
                    ('eats_small_game', BooleanListCodec()),
                    ('eats_big_game', BooleanListCodec()),
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
                '# billboards\n #'+'\t'.join('entity archetype zone x y z'.split()),
                PrimitiveListCodec(str),
                ObjectListCodec(BillboardPlacement,
                    ('archetype', PrimitiveListCodec(str)),
                    ('zone', PrimitiveListCodec(str)),
                    ('position', ContainerListCodec(glm.vec3, float, 3)),
                ),
            ),
            GameTableCodec(
                '# boxes\n# '+'\t'.join('entity archetype zone x y z'.split()),
                PrimitiveListCodec(str),
                ObjectListCodec(BoxPlacement,
                    ('archetype', PrimitiveListCodec(str)),
                    ('zone', PrimitiveListCodec(str)),
                    ('position', ContainerListCodec(glm.vec3, float, 3)),
                ),
            ),
            GameTableCodec('# physics\n #'+'\t'.join('entity vertical_velocity is_grounded'.split()), 
                PrimitiveListCodec(str),
                ObjectListCodec(VerticalPhysics,
                    ('vertical_velocity', PrimitiveListCodec(float)),
                    ('is_grounded', BooleanListCodec()))),
            GameTableCodec('# actor_states\n #'+'\t'.join('entity facing_x facing_y animation elapsed hurt tired asleep hot cold angry sad afraid happy'.split()), 
                PrimitiveListCodec(str),
                ObjectListCodec(CharacterAnimationState,
                    ('facing', ContainerListCodec(glm.vec2, float, 2)),
                    ('animation', PrimitiveListCodec(str)),
                    ('elapsed', PrimitiveListCodec(float)),
                    ('hurt', BooleanListCodec()),
                    ('tired', BooleanListCodec()),
                    ('asleep', BooleanListCodec()),
                    ('hot', BooleanListCodec()),
                    ('cold', BooleanListCodec()),
                    ('angry', BooleanListCodec()),
                    ('sad', BooleanListCodec()),
                    ('afraid', BooleanListCodec()),
                    ('happy', BooleanListCodec()),
                ),
            ),
            GameTableCodec(
                '# inventory\n #'+'\t'.join('character item quantity'.split()),
                ConcatenatedContainerCodec(tuple, PrimitiveListCodec(str), PrimitiveListCodec(str)),
                PrimitiveListCodec(int),
            ),
        ),
        DelimitedStringsCodec(table_delimiter, table_regex_delimiter, postfixed=True),
    )
