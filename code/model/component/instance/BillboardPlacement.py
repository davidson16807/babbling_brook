# HUMAN VETTED

from dataclasses import dataclass

from pyglm import glm

from ...identifiers import ArchetypeId


@dataclass(frozen=True)
class BillboardPlacement:
    archetype: ArchetypeId
    zone: str
    position: glm.vec3
