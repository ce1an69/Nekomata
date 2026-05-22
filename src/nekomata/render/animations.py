"""Textual widget animation helpers."""

from __future__ import annotations

from textual.css.scalar import ScalarOffset
from textual.geometry import Offset


_OFFSET_ZERO = ScalarOffset.from_offset(Offset(0, 0))


def animate_entrance(
    widget,
    *,
    duration: float = 0.30,
    dy: int = 1,
    easing: str = "out_quint",
) -> None:
    """Fade-in + slide-in from a vertical offset. Respects animation_enabled."""
    if not widget.app.animation_enabled:
        return
    widget.styles.opacity = 0
    widget.styles.offset = Offset(0, dy)
    widget.styles.animate("opacity", 1.0, duration=duration, easing=easing)
    widget.styles.animate(
        "offset", _OFFSET_ZERO, duration=duration, easing=easing,
    )


def animate_exit(
    widget,
    *,
    duration: float = 0.22,
    dy: int = -1,
    easing: str = "out_quint",
    callback=None,
) -> None:
    """Fade-out + slide-out to a vertical offset. Respects animation_enabled."""
    if not widget.app.animation_enabled:
        if callback:
            callback()
        return
    widget.styles.animate("opacity", 0.0, duration=duration, easing=easing)
    widget.styles.animate(
        "offset",
        ScalarOffset.from_offset(Offset(0, dy)),
        duration=duration,
        easing=easing,
    )
    if callback:
        widget.set_timer(duration + 0.01, callback)


def animate_slide_horizontal(
    widget,
    *,
    dx: int = 4,
    duration: float = 0.30,
    easing: str = "out_quint",
) -> None:
    """Fade-in + slide from a horizontal offset. Respects animation_enabled."""
    if not widget.app.animation_enabled:
        return
    widget.styles.opacity = 0
    widget.styles.offset = Offset(dx, 0)
    widget.styles.animate("opacity", 1.0, duration=duration, easing=easing)
    widget.styles.animate(
        "offset", _OFFSET_ZERO, duration=duration, easing=easing,
    )
