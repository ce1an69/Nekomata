"""Nekomata TUI application — pixel-art cat tarot Textual app."""

from textual.app import App
from textual.binding import Binding
from textual.events import Resize

from nekomata.core.i18n import set_lang
from nekomata.core.render.terminal import get_render_mode
from nekomata.core.render.themes import set_default_theme
from nekomata.core.storage.config import AppConfig
from nekomata.tui.screens.home import HomeScreen


class NekomataApp(App):
    """Nekomata — Pixel-art cat tarot TUI application."""

    TITLE = "Nekomata"
    CSS_PATH = None

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
    ]

    # Catppuccin Mocha palette — registered as CSS variables so all
    # child widgets can reference them via $crust, $mauve, etc.
    _CATPPUCCIN_MOCHA: dict[str, str] = {
        "crust": "#11111b",
        "mantle": "#181825",
        "base": "#1e1e2e",
        "surface0": "#313244",
        "surface1": "#45475a",
        "surface2": "#585b70",
        "overlay0": "#6c7086",
        "subtext0": "#a6adc8",
        "subtext1": "#bac2de",
        "text": "#cdd6f4",
        "mauve": "#cba6f7",
        "lavender": "#b4befe",
        "pink": "#f5c2e7",
        "red": "#f38ba8",
        "peach": "#fab387",
        "teal": "#94e2d5",
        "gold": "#f9e2af",
    }

    def get_theme_variable_defaults(self) -> dict[str, str]:
        """Register Catppuccin Mocha colors as global CSS variables."""
        return dict(self._CATPPUCCIN_MOCHA)

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
