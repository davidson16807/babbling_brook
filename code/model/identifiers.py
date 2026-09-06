"""Identifiers and grid addresses; geometric quantities use PyGLM."""

from typing import TypeAlias

Coordinate: TypeAlias = tuple[int, int]
EntityId: TypeAlias = str | int | Coordinate
ArchetypeId: TypeAlias = str | int
