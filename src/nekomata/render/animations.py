"""Textual widget animation helpers."""

from textual.widgets import Static


async def animate_reveal(widget: Static, duration: float = 0.3) -> None:
    """Quick fade-in reveal effect via opacity animation."""
    widget.styles.opacity = 0
    widget.styles.animate("opacity", 1.0, duration=duration)
