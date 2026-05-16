from __future__ import annotations

from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static


SPREADS = [
    ("single", "spread-single", "单牌", "每日灵感"),
    ("past_present_future", "spread-past-present-future", "过去·现在·未来", "时间线三牌阵"),
    ("situation_action_result", "spread-situation-action-result", "处境·行动·结果", "问题分析"),
]


class SpreadSelectScreen(Screen):
    DEFAULT_CSS = """
    SpreadSelectScreen {
        align: center middle;
    }
    SpreadSelectScreen #prompt {
        text-align: center;
        margin-bottom: 2;
    }
    SpreadSelectScreen Button {
        width: 40;
        margin-bottom: 1;
    }
    """

    def compose(self):
        with Center():
            yield Static("请选择牌阵：", id="prompt")
            with Vertical():
                for key, btn_id, name, desc in SPREADS:
                    yield Button(f"{name} — {desc}", id=btn_id)
                yield Button("↩ 返回", id="back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        for key, btn_id, name, desc in SPREADS:
            if event.button.id == btn_id:
                self.dismiss(key)
                return
