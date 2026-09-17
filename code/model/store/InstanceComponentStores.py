# HUMAN VETTED

from dataclasses import dataclass, field

from ..component.instances import CharacterAnimationState, Motion, ObjectPlacement, VerticalPhysics
from ..identifiers import EntityId

'''
A "store" is the name chosen for this application to represent
data structures that own collections for many components of different yet related types.
These data structures are known as "stores" (plural)
"Stores" exist outside the ECS architecture, and systems are not aware of them,
since in order to make it easier to use code outside the code base,
a system should only operate on the fewest component collections needed to do its job. 
'''

@dataclass(frozen=True)
class InstanceComponentStores:
    placements: dict[EntityId, ObjectPlacement] = field(default_factory=dict)
    physics: dict[EntityId, VerticalPhysics] = field(default_factory=dict)
    characters: dict[EntityId, CharacterAnimationState] = field(default_factory=dict)
    motions: dict[EntityId, Motion] = field(default_factory=dict)
