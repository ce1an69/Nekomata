from __future__ import annotations

from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Input, Static


BANNER_LINES = [
    "  ███╗   ██╗███████╗ ██████╗ ███╗   ██╗",
    "  ████╗  ██║██╔════╝██╔═══██╗████╗  ██║",
    "  ██╔██╗ ██║█████╗  ██║   ██║██╔██╗ ██║",
    "  ██║╚██╗██║██╔══╝  ██║   ██║██║╚██╗██║",
    "  ██║ ╚████║███████╗╚██████╔╝██║ ╚████║",
    "  ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝",
    "        猫又塔罗 · 像素风猫咪占卜",
]

SLASH_COMMANDS = {
    "/browse": "card_browser",
    "/quit": "quit",
}


class HomeScreen(Screen):
    DEFAULT_CSS = """
    HomeScreen {
        align: center middle;
    }
    HomeScreen #title {
        text-align: center;
        margin-bottom: 2;
    }
    HomeScreen #input-area {
        width: 60;
        height: auto;
    }
    HomeScreen #prompt-input {
        width: 100%;
    }
    HomeScreen #hint {
        color: $text-disabled;
        text-align: center;
        margin-top: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._banner_idx = 0
        self._banner_timer = None

    def compose(self):
        with Center():
            yield Static("", id="title")
            with Vertical(id="input-area"):
                yield Input(
                    placeholder="> Ask the cats anything…",
                    id="prompt-input",
                )
                yield Static("/browse  /quit", id="hint")

    def on_mount(self) -> None:
        animation_enabled = getattr(self.app, "animation_enabled", True)
        if animation_enabled:
            self._banner_idx = 0
            self._banner_timer = self.set_interval(0.08, self._reveal_banner_line)
        else:
            self.query_one("#title", Static).update("\n".join(BANNER_LINES))

    def _reveal_banner_line(self) -> None:
        if self._banner_idx >= len(BANNER_LINES):
            if self._banner_timer is not None:
                self._banner_timer.stop()
                self._banner_timer = None
            return
        self._banner_idx += 1
        self.query_one("#title", Static).update(
            "\n".join(BANNER_LINES[: self._banner_idx])
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "prompt-input":
            return
        value = event.value.strip()
        if not value:
            return

        cmd = SLASH_COMMANDS.get(value.lower())
        if cmd == "card_browser":
            from nekomata.screens.card_browser import CardBrowserScreen
            self.app.push_screen(CardBrowserScreen())
            return
        if cmd == "quit":
            self.app.exit()
            return

        self.app.question = value
        from nekomata.screens.spread_select import SpreadSelectScreen
        self.app.push_screen(
            SpreadSelectScreen(), callback=self._on_spread_selected
        )

    def _on_spread_selected(self, spread_key: str) -> None:
        from nekomata.screens.reading import ReadingScreen
        self.app.spread_key = spread_key
        self.app.push_screen(ReadingScreen(spread_key, self.app.question))
