"""Instance components: per-entity state, keyed by EntityId.

Model data. No window, event-library, GPU, or filesystem dependencies.

Component tables are ordinary dictionaries. Treat stored GLM vectors as values:
systems/updaters replace them, never mutate their coordinates in place.
"""
from .BillboardPlacement import BillboardPlacement
from .BoxPlacement import BoxPlacement
from .CharacterAnimationState import CharacterAnimationState
from .VerticalPhysics import VerticalPhysics
