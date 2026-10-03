# HUMAN VETTED

from dataclasses import dataclass

from pyglm import glm

from ...identifiers import ArchetypeId


@dataclass(frozen=True)
class BillboardPlacement:
    archetype: ArchetypeId
    position: glm.vec3
    zone: str = ""
