"""Custom Message types for the DrawScreen event system.

Decouples phase transitions, stream lifecycle, and cross-component requests
(InterpretationDialog ↔ DetailPanel) by using typed Messages that flow through
Textual's message bus.

Reference: Harlequin's query pipeline pattern (QuerySubmitted -> ResultsFetched).
"""

from __future__ import annotations

from textual.message import Message

from nekomata.tui.screens.draw_phase import Phase

# -- Phase lifecycle --


class PhaseChanged(Message):
    """Posted when the draw screen phase transitions (PICK -> FLIP -> DONE)."""

    def __init__(self, old_phase: Phase, new_phase: Phase) -> None:
        self.old_phase = old_phase
        self.new_phase = new_phase
        super().__init__()


# -- Stream lifecycle (one-shot events; synchronous updates stay as callbacks) --


class StreamError(Message):
    """Stream encountered an error."""

    def __init__(self, message: str, config_error: bool = False) -> None:
        self.message = message
        self.config_error = config_error
        super().__init__()


class StreamDone(Message):
    """Stream finished successfully."""


# -- Detail panel --


class DetailShowRequested(Message):
    """Request to show the detail panel (optionally with a specific slot)."""

    def __init__(self, slot=None) -> None:
        self.slot = slot
        super().__init__()


class DetailHideRequested(Message):
    """Request to hide the detail panel."""

    def __init__(self, center_spread=None) -> None:
        self.center_spread = center_spread
        super().__init__()
