"""Nekomata TUI application entry point."""

from textual.app import App
from textual.events import Resize

from nekomata.render.styles import (
    C_BASE,
    C_CRUST,
    C_LAVENDER,
    C_MANTLE,
    C_MAUVE,
    C_SUBTEXT0,
    C_SURFACE0,
    C_SURFACE1,
    C_TEXT,
)
from nekomata.render.terminal import get_render_mode
from nekomata.render.themes import set_default_theme
from nekomata.screens.home import HomeScreen
from nekomata.storage.config import AppConfig


class NekomataApp(App):
    """Nekomata (猫又) — Pixel-art cat tarot TUI application."""

    TITLE = "Nekomata"
    CSS_PATH = None

    DEFAULT_CSS = f"""
    Screen {{
        background: {C_CRUST};
        color: {C_TEXT};
        padding: 1 2;
    }}
    Button {{
        background: {C_MANTLE};
        color: {C_SUBTEXT0};
        border: round {C_SURFACE0};
        padding: 0 2;
        min-width: 12;
        transition: background 180ms, border 180ms, color 180ms;
    }}
    Button:hover {{
        background: {C_BASE};
        color: {C_TEXT};
        border: round {C_SURFACE1};
    }}
    Button:focus {{
        background: {C_BASE};
        border: round {C_MAUVE};
        color: {C_TEXT};
        text-style: bold;
    }}
    Button.-primary {{
        background: {C_BASE};
        border: round {C_MAUVE};
        color: {C_MAUVE};
    }}
    Button.-primary:hover {{
        background: {C_SURFACE0};
    }}
    Button.-primary:focus {{
        background: {C_SURFACE0};
        text-style: bold;
    }}
    Button.-success {{
        background: {C_BASE};
        border: round {C_LAVENDER};
        color: {C_LAVENDER};
    }}
    Button.-success:hover {{
        background: {C_SURFACE0};
    }}
    Button.-success:disabled {{
        opacity: 0.5;
    }}
    Input {{
        background: {C_BASE};
        color: {C_TEXT};
        border: round {C_SURFACE1};
        transition: background 180ms, border 180ms;
    }}
    Input:focus {{
        border: round {C_MAUVE};
    }}
    VerticalScroll {{
        scrollbar-background: {C_MANTLE};
        scrollbar-color: {C_SURFACE1};
    }}
    """

    def __init__(self) -> None:
        super().__init__()
        self.question: str = ""
        self.spread_key: str = ""
        self.spread_name: str = ""
        self.render_mode: str = "compact"
        self.config: AppConfig = AppConfig.load()
        self.animation_enabled: bool = True
        self.reversal_prob: float = 0.5
        self.theme_name: str = "catppuccin"

    def on_mount(self) -> None:
        """Detect terminal capabilities and push the home screen."""
        self.render_mode = get_render_mode()
        set_default_theme(self.theme_name)
        self.push_screen(HomeScreen())
        if not AppConfig.config_exists():
            from nekomata.screens.setup import SetupScreen
            self.push_screen(SetupScreen(), callback=self._on_setup_done)

    def _on_setup_done(self, _result: None) -> None:
        """Transition from setup screen to home screen."""
        from nekomata.screens.home import HomeScreen
        if isinstance(self.screen, HomeScreen):
            self.screen.resume()

    def on_resize(self, event: Resize) -> None:
        """Re-detect render mode when terminal is resized."""
        self.render_mode = get_render_mode()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="nekomata")
    parser.add_argument("--web", action="store_true", help="Launch web UI")
    parser.add_argument("--port", type=int, default=8080, help="Web server port")
    args = parser.parse_args()

    if args.web:
        from nekomata.web.server import start_web_server
        start_web_server(port=args.port)
    else:
        app = NekomataApp()
        app.run()


if __name__ == "__main__":
    main()
