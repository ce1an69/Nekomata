"""Card rendering color themes (Catppuccin-based)."""

from dataclasses import dataclass


@dataclass
class CardTheme:
    """Color theme for card rendering."""
    upright_border: str = "yellow"
    reversed_border: str = "blue"
    title_style: str = "bold"
    keyword_style: str = "bold"
    background: str = ""


THEMES: dict[str, CardTheme] = {
    "dark": CardTheme(
        upright_border="yellow",
        reversed_border="blue",
    ),
    "light": CardTheme(
        upright_border="bright_yellow",
        reversed_border="bright_blue",
    ),
    "cat": CardTheme(
        upright_border="color(180)",
        reversed_border="color(75)",
    ),
    "catppuccin": CardTheme(
        upright_border="#f9e2af",
        reversed_border="#89b4fa",
        title_style="bold #b4befe",
        keyword_style="bold #fab387",
    ),
}

# Module-level default, set from AppConfig on app startup
_default_name: str = "catppuccin"


def set_default_theme(name: str) -> None:
    """Set the global default theme name (called once during app init)."""
    global _default_name
    _default_name = name if name in THEMES else "catppuccin"


def get_theme(name: str | None = None) -> CardTheme:
    """Return the named theme, or the global default if name is None."""
    return THEMES.get(name or _default_name, THEMES["catppuccin"])
