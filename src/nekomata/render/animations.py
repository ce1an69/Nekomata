"""Textual widget animation helpers."""

from textual.css.scalar import ScalarOffset
from textual.geometry import Offset
from textual.widgets import Static

_OFFSET_ZERO = ScalarOffset.from_offset(Offset(0, 0))


def animate_fade_in(widget, duration: float = 0.25) -> None:
    """Simple opacity fade-in."""
    widget.styles.opacity = 0
    widget.styles.animate("opacity", 1.0, duration=duration, easing="out_cubic")
