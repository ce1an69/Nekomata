"""Textual widget animation helpers."""

from textual.css.scalar import ScalarOffset
from textual.dom import DOMNode
from textual.geometry import Offset
from textual.widgets import Static

_OFFSET_ZERO = ScalarOffset.from_offset(Offset(0, 0))


async def animate_reveal(widget: Static, duration: float = 0.3) -> None:
    """Quick fade-in reveal effect via opacity animation."""
    widget.styles.opacity = 0
    widget.styles.animate("opacity", 1.0, duration=duration)


def animate_slide_in(
    widget: DOMNode,
    duration: float = 0.32,
    direction: int = 1,
    delay: float = 0.0,
) -> None:
    """Slide + fade entrance for a widget.

    Args:
        widget: The widget to animate.
        duration: Animation duration in seconds.
        direction: 1 = slide up from below, -1 = slide down from above.
        delay: Delay before animation starts (use set_timer externally for stagger).
    """
    widget.styles.opacity = 0
    widget.styles.offset = (0, direction)
    easing = "out_cubic"
    widget.styles.animate("opacity", 1.0, duration=duration, easing=easing)
    widget.styles.animate("offset", _OFFSET_ZERO, duration=duration, easing=easing)


def animate_fade_in(widget: DOMNode, duration: float = 0.25) -> None:
    """Simple opacity fade-in."""
    widget.styles.opacity = 0
    widget.styles.animate("opacity", 1.0, duration=duration, easing="out_cubic")
