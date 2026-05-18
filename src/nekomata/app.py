"""Nekomata TUI application entry point."""

from textual.app import App
from textual.events import Resize

from nekomata.render.terminal import get_render_mode
from nekomata.render.themes import set_default_theme
from nekomata.screens.home import HomeScreen
from nekomata.storage.config import AppConfig


class NekomataApp(App):
    """Nekomata (猫又) — Pixel-art cat tarot TUI application."""

    TITLE = "Nekomata"
    CSS_PATH = None

    DEFAULT_CSS = """
    Screen {
        background: #11111b;
        color: #cdd6f4;
        padding: 1 2;
    }
    Button {
        background: #181825;
        color: #a6adc8;
        border: round #313244;
        padding: 0 2;
        min-width: 12;
        transition: background 180ms, border 180ms, color 180ms;
    }
    Button:hover {
        background: #1e1e2e;
        color: #cdd6f4;
        border: round #45475a;
    }
    Button:focus {
        background: #1e1e2e;
        border: round #cba6f7;
        color: #cdd6f4;
        text-style: bold;
    }
    Button.-primary {
        background: #1e1e2e;
        border: round #cba6f7;
        color: #cba6f7;
    }
    Button.-primary:hover {
        background: #313244;
    }
    Button.-primary:focus {
        background: #313244;
        text-style: bold;
    }
    Button.-success {
        background: #1e1e2e;
        border: round #b4befe;
        color: #b4befe;
    }
    Button.-success:hover {
        background: #313244;
    }
    Button.-success:disabled {
        opacity: 0.5;
    }
    Input {
        background: #1e1e2e;
        color: #cdd6f4;
        border: round #45475a;
        transition: background 180ms, border 180ms;
    }
    Input:focus {
        border: round #cba6f7;
    }
    VerticalScroll {
        scrollbar-background: #181825;
        scrollbar-color: #45475a;
    }
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
    app = NekomataApp()
    app.run()


if __name__ == "__main__":
    main()
