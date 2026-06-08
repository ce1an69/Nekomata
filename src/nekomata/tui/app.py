"""Nekomata TUI application — pixel-art cat tarot Textual app."""

from textual.app import App
from textual.binding import Binding
from textual.events import Resize

from nekomata.core.i18n import set_lang
from nekomata.core.render.styles import (
    C_BASE,
    C_CRUST,
    C_GOLD,
    C_LAVENDER,
    C_MANTLE,
    C_MAUVE,
    C_OVERLAY0,
    C_PEACH,
    C_PINK,
    C_RED,
    C_SUBTEXT0,
    C_SUBTEXT1,
    C_SURFACE0,
    C_SURFACE1,
    C_SURFACE2,
    C_TEAL,
    C_TEXT,
)
from nekomata.core.render.terminal import get_render_mode
from nekomata.core.render.themes import set_default_theme
from nekomata.core.storage.config import AppConfig
from nekomata.tui.screens.home import HomeScreen

# Single Catppuccin Mocha palette — built from styles.py constants.
# All TUI CSS variables (e.g. $crust, $mauve) resolve to these values.
_CATPPUCCIN_MOCHA: dict[str, str] = {
    "crust": C_CRUST,
    "mantle": C_MANTLE,
    "base": C_BASE,
    "surface0": C_SURFACE0,
    "surface1": C_SURFACE1,
    "surface2": C_SURFACE2,
    "overlay0": C_OVERLAY0,
    "subtext0": C_SUBTEXT0,
    "subtext1": C_SUBTEXT1,
    "text": C_TEXT,
    "mauve": C_MAUVE,
    "lavender": C_LAVENDER,
    "pink": C_PINK,
    "red": C_RED,
    "peach": C_PEACH,
    "teal": C_TEAL,
    "gold": C_GOLD,
}


class NekomataApp(App):
    """Nekomata — Pixel-art cat tarot TUI application."""

    TITLE = "Nekomata"
    CSS_PATH = None

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
    ]

    def get_theme_variable_defaults(self) -> dict[str, str]:
        """Register Catppuccin Mocha colors as global CSS variables."""
        return dict(_CATPPUCCIN_MOCHA)

    DEFAULT_CSS = """
    Screen {
        background: $crust;
        color: $text;
        padding: 1 2;
    }
    Button {
        background: $mantle;
        color: $subtext0;
        border: round $surface0;
        padding: 0 2;
        min-width: 12;
        transition: background 180ms, border 180ms, color 180ms;
    }
    Button:hover {
        background: $base;
        color: $text;
        border: round $surface1;
    }
    Button:focus {
        background: $base;
        border: round $mauve;
        color: $text;
        text-style: bold;
    }
    Button.-primary {
        background: $base;
        border: round $mauve;
        color: $mauve;
    }
    Button.-primary:hover {
        background: $surface0;
    }
    Button.-primary:focus {
        background: $surface0;
        text-style: bold;
    }
    Button.-success {
        background: $base;
        border: round $lavender;
        color: $lavender;
    }
    Button.-success:hover {
        background: $surface0;
    }
    Button.-success:disabled {
        opacity: 0.5;
    }
    Input {
        background: $base;
        color: $text;
        border: round $surface1;
        transition: background 180ms, border 180ms;
    }
    Input:focus {
        border: round $mauve;
    }
    VerticalScroll {
        scrollbar-background: $mantle;
        scrollbar-color: $surface1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.question: str = ""
        self.spread_key: str = ""
        self.render_mode: str = "compact"
        self.config: AppConfig = AppConfig.load()
        set_lang(self.config.lang)
        self.animation_enabled: bool = True
        self.reversal_prob: float = 0.5
        self.theme_name: str = "catppuccin"

    def on_mount(self) -> None:
        """Detect terminal capabilities and push the home screen."""
        self.render_mode = get_render_mode()
        set_default_theme(self.theme_name)
        self.push_screen(HomeScreen())
        if not AppConfig.config_exists():
            from nekomata.tui.screens.setup import SetupScreen

            self.push_screen(SetupScreen(), callback=self._on_setup_done)

    def _on_setup_done(self, _result: None) -> None:
        """Transition from setup screen to home screen."""
        if not AppConfig.config_exists():
            from nekomata.tui.screens.setup import SetupScreen

            self.push_screen(SetupScreen(), callback=self._on_setup_done)
            return
        from nekomata.tui.screens.home import HomeScreen

        if isinstance(self.screen, HomeScreen):
            self.screen.resume()

    def on_resize(self, event: Resize) -> None:
        """Re-detect render mode when terminal is resized."""
        self.render_mode = get_render_mode()
