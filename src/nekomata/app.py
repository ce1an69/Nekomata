from __future__ import annotations

from textual.app import App

from nekomata.render.terminal import get_render_mode
from nekomata.screens.home import HomeScreen
from nekomata.storage.config import AppConfig


class NekomataApp(App):
    TITLE = "Nekomata — 猫又塔罗"
    CSS_PATH = None

    def __init__(self) -> None:
        super().__init__()
        self.question: str = ""
        self.spread_key: str = ""
        self.spread_name: str = ""
        self.spread_name_zh: str = ""
        self.render_mode: str = "compact"
        self._config = AppConfig.load()
        self.animation_enabled: bool = self._config.display_animation
        self.reversal_prob: float = self._config.reversal_prob

    def on_mount(self) -> None:
        self.render_mode = get_render_mode()
        self.push_screen(HomeScreen())

    def on_resize(self, event) -> None:
        self.render_mode = get_render_mode()


def main() -> None:
    app = NekomataApp()
    app.run()


if __name__ == "__main__":
    main()
