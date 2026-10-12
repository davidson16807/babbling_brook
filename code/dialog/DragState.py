"""The ids of the dialog's drag types, as in xcraft's `DragState`; see ConstituentDrags.py."""
from enum import Enum


class DragState(Enum):
    released = 'released'
    constituent = 'constituent'
