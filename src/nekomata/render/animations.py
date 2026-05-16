from __future__ import annotations

from inspect import isawaitable

from textual.widgets import Static


async def _run_animation(result) -> None:
    if isawaitable(result):
        await result


async def animate_slide_in(widget: Static, duration: float = 0.5) -> None:
    """Slide a widget in from below with opacity fade."""
    widget.styles.offset = (0, 3)
    widget.styles.opacity = 0
    await _run_animation(widget.styles.animate("opacity", 1.0, duration=duration))
    await _run_animation(widget.styles.animate("offset", (0, 0), duration=duration))


async def animate_reveal(widget: Static, duration: float = 0.3) -> None:
    """Quick fade-in reveal effect."""
    widget.styles.opacity = 0
    await _run_animation(widget.styles.animate("opacity", 1.0, duration=duration))


async def animate_shuffle(widget: Static) -> None:
    """Quick horizontal shake effect."""
    widget.styles.offset = (0, 0)
    await _run_animation(widget.styles.animate("offset", (2, 0), duration=0.05))
    await _run_animation(widget.styles.animate("offset", (-2, 0), duration=0.05))
    await _run_animation(widget.styles.animate("offset", (0, 0), duration=0.05))
