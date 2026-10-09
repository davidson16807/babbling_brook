from dataclasses import dataclass


@dataclass(frozen=True)
class Actionable:
    """Marks an entity as interactable; `action` names an `ActionRegistry` entry."""
    action: str

    def __post_init__(self):
        if not self.action.strip():
            raise ValueError("action must not be blank")
