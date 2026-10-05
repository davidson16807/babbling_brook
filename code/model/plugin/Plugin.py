# HUMAN VETTED

from collections.abc import Iterator, Sequence

from dataclasses import dataclass, field
from typing import ClassVar, overload

from ..component.archetype import (BillboardArchetype, TileArchetype, BoxArchetype, CharacterArchetype,
                                   CreatureArchetype, Liquid, SeasonalTileArchetype,
                                   Waypoint, CardinalWaypoint)
from ..component.Cycle import Cycle
from ..component.zone import Biome, Zone, ZoneDirections, ZoneAdjacency, Waterlevel
from ..component.Landmark import Landmark
from ..component.instance import CharacterAnimationState, BillboardPlacement, BoxPlacement, VerticalPhysics
from ..identifiers import ArchetypeId, EntityId

AnimationFrameId = tuple[ArchetypeId, str, int, int]
AnimationFrame = tuple[str, float]

"""
A `Plugin` represents all of `GameState` that cannot be represented within `Map`s.
This is effectively all dictionaries for storing ECS components 
and values for things like global variables and map palettes.
`Plugin`s have interesting structure in that there is an `update` function
such that one plugin can be updated with the contents of another.
This allows plugins to serve several roles: they represent file contents for
game data, mods, and save states. This is why the `Plugin` is chosen. 
See `PluginOps` for operations you can perform on `Plugin`s like `update`.
"""

@dataclass(frozen=True)
class Plugin(Sequence[dict | set]):

    format: dict[str, int] = field(default_factory=dict)
    globals: dict[str, float] = field(default_factory=dict)
    cycles: dict[str, Cycle] = field(default_factory=dict)
    biomes: dict[str, Biome] = field(default_factory=dict)
    biome_spawns: set[tuple[str, str]] = field(default_factory=set)
    zones: dict[str, Zone] = field(default_factory=dict)
    zone_directions: dict[str, ZoneDirections] = field(default_factory=dict)
    zone_adjacencies: dict[tuple[str, str], ZoneAdjacency] = field(default_factory=dict)
    cardinal_waypoints: dict[str, CardinalWaypoint] = field(default_factory=dict)
    colorcodes: dict[str, str] = field(default_factory=dict)
    inventory: dict[tuple[EntityId, str], int] = field(default_factory=dict)
    tiles: dict[ArchetypeId, TileArchetype] = field(default_factory=dict)
    box_archetypes: dict[ArchetypeId, BoxArchetype] = field(default_factory=dict)
    billboard_archetypes: dict[ArchetypeId, BillboardArchetype] = field(default_factory=dict)
    character_archetypes: dict[ArchetypeId, CharacterArchetype] = field(default_factory=dict)
    creatures: dict[ArchetypeId, CreatureArchetype] = field(default_factory=dict)
    liquids: dict[ArchetypeId, Liquid] = field(default_factory=dict)
    waypoints: dict[ArchetypeId, Waypoint] = field(default_factory=dict)
    animation_frames: dict[AnimationFrameId, AnimationFrame] = field(default_factory=dict)
    tile_palette: dict[int, ArchetypeId] = field(default_factory=dict)
    object_palette: dict[int, ArchetypeId] = field(default_factory=dict)
    billboards: dict[EntityId, BillboardPlacement] = field(default_factory=dict)
    boxes: dict[EntityId, BoxPlacement] = field(default_factory=dict)
    physics: dict[EntityId, VerticalPhysics] = field(default_factory=dict)
    characters: dict[EntityId, CharacterAnimationState] = field(default_factory=dict)
    landmarks: dict[str, Landmark] = field(default_factory=dict)
    waterlevels: dict[str, Waterlevel] = field(default_factory=dict)

    seasonal_tiles: dict[ArchetypeId, SeasonalTileArchetype] = field(default_factory=dict)
    seasonal_billboards: dict[tuple[ArchetypeId, int], str] = field(default_factory=dict)

    table_fields: ClassVar[tuple[str, ...]] = (
        'format',
        'globals',
        'cycles',
        'biomes',
        'biome_spawns',
        'zones',
        'waterlevels',
        'zone_directions',
        'zone_adjacencies',
        'waypoints',
        'cardinal_waypoints',
        'landmarks',
        'colorcodes',
        'tiles',
        'liquids',
        'seasonal_tiles',
        'billboard_archetypes',
        'box_archetypes',
        'seasonal_billboards',
        'character_archetypes',
        'creatures',
        'animation_frames',
        'tile_palette',
        'object_palette',
        'billboards',
        'boxes',
        'physics',
        'characters',
        'inventory',
    )

    @classmethod
    def from_tables(cls, tables: Sequence[dict | set]) -> 'Plugin':
        if len(tables) != len(cls.table_fields):
            raise ValueError(
                f"A plugin must contain {len(cls.table_fields)} tables; got {len(tables)}"
            )
        return cls(**{name: set(table) if isinstance(table, (set, frozenset)) else dict(table)
                      for name, table in zip(cls.table_fields, tables)})

    def to_tables(self) -> list[dict | set]:
        return [getattr(self, name) for name in self.table_fields]

    def __len__(self) -> int:
        return len(self.table_fields)

    @overload
    def __getitem__(self, index: int) -> dict | set: ...

    @overload
    def __getitem__(self, index: slice) -> list[dict | set]: ...

    def __getitem__(self, index: int | slice) -> dict | set | list[dict | set]:
        return self.to_tables()[index]

    def __iter__(self) -> Iterator[dict | set]:
        return iter(self.to_tables())
