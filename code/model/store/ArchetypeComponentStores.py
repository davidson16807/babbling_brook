# HUMAN VETTED

from dataclasses import dataclass, field

from ..component.archetypes import (CharacterArchetype, BillboardArchetype, TileArchetype, BoxArchetype,
                                    AnimalArchetype, Liquid, Waypoint, SeasonalTileArchetype)
from ..identifiers import ArchetypeId

'''
A "store" is the name chosen for this application to represent
data structures that own collections for many components of different yet related types.
These data structures are known as "stores" (plural)
"Stores" exist outside the ECS architecture, and systems are not aware of them,
since in order to make it easier to use code outside the code base,
a system should only operate on the fewest component collections needed to do its job. 
'''

@dataclass(frozen=True)
class ArchetypeComponentStores:
    billboards: dict[ArchetypeId, BillboardArchetype] = field(default_factory=dict)
    characters: dict[ArchetypeId, CharacterArchetype] = field(default_factory=dict)
    tiles: dict[ArchetypeId, TileArchetype] = field(default_factory=dict)
    animals: dict[ArchetypeId, AnimalArchetype] = field(default_factory=dict)
    liquids: dict[ArchetypeId, Liquid] = field(default_factory=dict)
    waypoints: dict[ArchetypeId, Waypoint] = field(default_factory=dict)
    seasonal_tiles: dict[ArchetypeId, SeasonalTileArchetype] = field(default_factory=dict)
    seasonal_billboards: dict[tuple[ArchetypeId, int], str] = field(default_factory=dict)
    boxes: dict[ArchetypeId, BoxArchetype] = field(default_factory=dict)
