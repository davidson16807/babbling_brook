# HUMAN VETTED

from dataclasses import dataclass

from pyglm import glm

from ...identifiers import ArchetypeId


@dataclass(frozen=True)
class BoxPlacement:
    """A box archetype instance positioned at its bottom-center."""
    archetype: ArchetypeId
    position: glm.vec3
    zone: str = ""
