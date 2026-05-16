from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CardTheme:
    """Color theme for card rendering."""
    upright_border: str = "yellow"
    reversed_border: str = "blue"
    summary_border: str = "magenta"
    title_style: str = "bold"
    keyword_style: str = "bold"
    background: str = ""


THEMES: dict[str, CardTheme] = {
    "dark": CardTheme(
        upright_border="yellow",
        reversed_border="blue",
        summary_border="magenta",
    ),
    "light": CardTheme(
        upright_border="bright_yellow",
        reversed_border="bright_blue",
        summary_border="bright_magenta",
    ),
    "cat": CardTheme(
        upright_border="color(180)",
        reversed_border="color(75)",
        summary_border="color(213)",
    ),
}


def get_theme(name: str = "dark") -> CardTheme:
    return THEMES.get(name, THEMES["dark"])
