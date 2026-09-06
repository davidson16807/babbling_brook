# HUMAN VETTED

from dataclasses import dataclass, field

'''
A "store" is the name chosen for this application to represent
data structures that own collections for many components of different yet related types.
These data structures are known as "stores" (plural)
"Stores" exist outside the ECS architecture, and systems are not aware of them,
since in order to make it easier to use code outside the code base,
a system should only operate on the fewest component collections needed to do its job. 
'''

EntityId: TypeAlias = str | int

@dataclass(frozen=True)
class InstanceComponentStores:
    positionables: dict[EntityId, glm.vec3] = field(default_factory=dict)
    archetyped: dict[EntityId, ArchetypeId] = field(default_factory=dict)
    physics: dict[EntityId, VerticalPhysics] = field(default_factory=dict)
    characters: dict[EntityId, CharacterState] = field(default_factory=dict)

ArchetypeId: TypeAlias = str | int

@dataclass(frozen=True)
class ArchetypeComponentStores:
    objects: dict[ArchetypeId, ObjectArchetype] = field(default_factory=dict)
    characters: dict[ArchetypeId, CharacterArchetype] = field(default_factory=dict)
    tiles: dict[ArchetypeId, TileArchetype] = field(default_factory=dict)
