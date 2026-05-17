"""Nekomata TUI application entry point."""

from textual.app import App
from textual.events import Resize

from nekomata.render.terminal import get_render_mode
from nekomata.render.themes import set_default_theme
from nekomata.screens.home import HomeScreen
from nekomata.storage.config import AppConfig


class NekomataApp(App):
    """Nekomata (猫又) — Pixel-art cat tarot TUI application."""

    TITLE = "Nekomata — 猫又塔罗"
    CSS_PATH = None

    DEFAULT_CSS = """
    Screen {
        background: #11111b;
        color: #cdd6f4;
    }
    Button {
        background: #1e1e2e;
        color: #cdd6f4;
        border: tall #45475a;
        padding: 0 2;
    }
    Button:hover {
        background: #313244;
        border: tall #585b70;
    }
    Button:focus {
        border: tall #cba6f7;
        text-style: bold;
    }
    Button.-primary {
        background: #1e1e2e;
        border: tall #cba6f7;
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
        border: tall #a6e3a1;
        color: #a6e3a1;
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
    }
    Input:focus {
        border: tall #cba6f7;
    }
    VerticalScroll {
        scrollbar-background: #1e1e2e;
        scrollbar-color: #45475a;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.question: str = ""
        self.spread_key: str = ""
        self.spread_name: str = ""
        self.spread_name_zh: str = ""
        self.render_mode: str = "compact"
        self.config: AppConfig = AppConfig.load()
        self.animation_enabled: bool = self.config.display_animation
        self.reversal_prob: float = self.config.reversal_prob
        self.theme_name: str = self.config.display_theme

    def on_mount(self) -> None:
        """Detect terminal capabilities and push the home screen."""
        self.render_mode = get_render_mode()
        set_default_theme(self.theme_name)
        self.push_screen(HomeScreen())

    def on_resize(self, event: Resize) -> None:
        """Re-detect render mode when terminal is resized."""
        self.render_mode = get_render_mode()


def main() -> None:
    app = NekomataApp()
    app.run()


if __name__ == "__main__":
    main()
