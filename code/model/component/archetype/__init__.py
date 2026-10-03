"""Archetype components: shared definitions that instances refer to by ArchetypeId.

Application data. No window, event-library, GPU, or filesystem dependencies.

Component tables are ordinary dictionaries. Treat stored GLM vectors as values:
systems/updaters replace them, never mutate their coordinates in place.
"""
from .BillboardArchetype import BillboardArchetype
from .BoxArchetype import BoxArchetype
from .CardinalWaypoint import CardinalWaypoint
from .CharacterArchetype import CharacterArchetype
from .CreatureArchetype import CreatureArchetype
from .Liquid import Liquid
from .SeasonalTileArchetype import SeasonalTileArchetype
from .TileArchetype import TileArchetype
from .Waypoint import Waypoint
