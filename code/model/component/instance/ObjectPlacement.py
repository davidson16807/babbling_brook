from dataclasses import dataclass

from pyglm import glm

from ...identifiers import ArchetypeId


@dataclass(frozen=True)
class ObjectPlacement:
    """An archetype instance positioned at its bottom-center.

    Every placed entity shares this component and one entity-keyed table.
    How it renders and collides comes from its archetype's other components:
    a billboard component, a box component, both, or neither.
    """
    archetype: ArchetypeId
    zone: str
    position: glm.vec3
