from dataclasses import dataclass

from pyglm import glm

from ...identifiers import ArchetypeId


@dataclass(frozen=True)
class ObjectPlacement:
    """An archetype instance positioned at its bottom-center.

    Billboards and boxes share this component and one entity-keyed table.
    Whether an entity renders and collides as a billboard or as a box is
    decided by which archetype table defines its archetype.
    """
    archetype: ArchetypeId
    zone: str
    position: glm.vec3
