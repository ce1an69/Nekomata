from __future__ import annotations

from textual.app import App

from nekomata.screens.home import HomeScreen


class NekomataApp(App):
    TITLE = "Nekomata — 猫又塔罗"
    CSS_PATH = None

    def __init__(self) -> None:
        super().__init__()
        self.question: str = ""
        self.spread_key: str = ""
        self.spread_name: str = ""
        self.spread_name_zh: str = ""

    def on_mount(self) -> None:
        self.push_screen(HomeScreen())


def main() -> None:
    app = NekomataApp()
    app.run()


if __name__ == "__main__":
    main()
