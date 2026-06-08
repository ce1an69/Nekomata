"""Textual widget animation helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from textual.css.scalar import ScalarOffset
from textual.geometry import Offset

if TYPE_CHECKING:
    from textual.timer import Timer

_OFFSET_ZERO = ScalarOffset.from_offset(Offset(0, 0))


def animate_entrance(
    widget,
    *,
    duration: float = 0.30,
    dx: int = 0,
    dy: int = 1,
    easing: str = "out_quint",
) -> None:
    """Fade-in + slide-in from an offset. Respects animation_enabled."""
    if not widget.app.animation_enabled:
        widget.styles.opacity = 1
        widget.styles.offset = Offset(0, 0)
        return
    widget.styles.opacity = 0
    widget.styles.offset = Offset(dx, dy)
    widget.styles.animate("opacity", 1.0, duration=duration, easing=easing)
    widget.styles.animate(
        "offset",
        _OFFSET_ZERO,
        duration=duration,
        easing=easing,
    )


def animate_exit(
    widget,
    *,
    duration: float = 0.22,
    dx: int = 0,
    dy: int = -1,
    easing: str = "out_quint",
    callback: Callable | None = None,
) -> Timer | None:
    """Fade-out + slide-out to an offset. Respects animation_enabled.

    Returns the internal timer (if any), so callers can cancel the callback.
    """
    if not widget.app.animation_enabled:
        if callback:
            callback()
        return None
    widget.styles.animate("opacity", 0.0, duration=duration, easing=easing)
    widget.styles.animate(
        "offset",
        ScalarOffset.from_offset(Offset(dx, dy)),
        duration=duration,
        easing=easing,
    )
    if callback:
        return widget.set_timer(duration + 0.01, callback)
    return None


def staggered_entrance(
    screen,
    widgets: list,
    *,
    stagger: float = 0.04,
    duration: float = 0.30,
    dx: int = 0,
    dy: int = 1,
    easing: str = "out_quint",
    initial_delay: float = 0.01,
    on_complete: Callable | None = None,
) -> None:
    """Animate a list of widgets appearing one-by-one with staggered timing.

    Sets each widget to invisible, then reveals them one at a time with
    entrance animation. Optionally calls *on_complete* after all animations finish.
    Respects animation_enabled.
    """
    if not screen.app.animation_enabled:
        for w in widgets:
            w.styles.opacity = 1
            w.styles.offset = Offset(0, 0)
        if on_complete:
            screen.set_timer(0.01, on_complete)
        return
    for w in widgets:
        w.styles.opacity = 0
        w.styles.offset = Offset(dx, dy)
    target = _OFFSET_ZERO
    for i, w in enumerate(widgets):
        screen.set_timer(
            initial_delay + i * stagger,
            lambda _w=w: (
                _w.styles.animate("opacity", 1.0, duration=duration, easing=easing),
                _w.styles.animate("offset", target, duration=duration, easing=easing),
            ),
        )
    if on_complete:
        total = initial_delay + len(widgets) * stagger + duration + 0.05
        screen.set_timer(total, on_complete)
