from __future__ import annotations

from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static


BANNER = r"""
  ███╗   ██╗███████╗ ██████╗ ███╗   ██╗
  ████╗  ██║██╔════╝██╔═══██╗████╗  ██║
  ██╔██╗ ██║█████╗  ██║   ██║██╔██╗ ██║
  ██║╚██╗██║██╔══╝  ██║   ██║██║╚██╗██║
  ██║ ╚████║███████╗╚██████╔╝██║ ╚████║
  ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
        猫又塔罗 · 像素风猫咪占卜
"""


class HomeScreen(Screen):
    DEFAULT_CSS = """
    HomeScreen {
        align: center middle;
    }
    HomeScreen #banner {
        text-align: center;
        margin-bottom: 2;
    }
    HomeScreen Vertical {
        width: auto;
        height: auto;
    }
    HomeScreen Button {
        width: 30;
        margin-bottom: 1;
    }
    """

    def compose(self):
        with Center():
            yield Static(BANNER, id="title")
            with Vertical():
                yield Button("🔮 开始占卜", id="start-reading", variant="primary")
                yield Button("📚 牌库浏览", id="card-browser")
                yield Button("📓 历史记录", id="journal")
                yield Button("❌ 退出", id="quit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        from nekomata.screens.spread_select import SpreadSelectScreen

        match event.button.id:
            case "start-reading":
                self.app.push_screen(SpreadSelectScreen(), callback=self._on_spread_selected)
            case "quit":
                self.app.exit()

    def _on_spread_selected(self, spread_key: str) -> None:
        from nekomata.screens.question import QuestionScreen
        self.app.push_screen(QuestionScreen(spread_key))
