"""Draw screen phase enum — shared by all draw sub-modules."""

from enum import Enum, auto


class Phase(Enum):
    """Draw screen state machine: PICK -> FLIP -> DONE."""

    PICK = auto()
    FLIP = auto()
    DONE = auto()
