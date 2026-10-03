# HUMAN VETTED

from dataclasses import dataclass, field

from ..component.instance import CharacterAnimationState, BillboardPlacement, BoxPlacement, VerticalPhysics
from ..identifiers import EntityId
from ..component.Cycle import Cycle
from ..component.Landmark import Landmark
from ..component.Waterlevel import Waterlevel

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
    billboards: dict[EntityId, BillboardPlacement] = field(default_factory=dict)
    physics: dict[EntityId, VerticalPhysics] = field(default_factory=dict)
    characters: dict[EntityId, CharacterAnimationState] = field(default_factory=dict)
    cycles: dict[str, Cycle] = field(default_factory=dict)
    landmarks: dict[str, Landmark] = field(default_factory=dict)
    waterlevels: dict[str, Waterlevel] = field(default_factory=dict)
    boxes: dict[EntityId, BoxPlacement] = field(default_factory=dict)
