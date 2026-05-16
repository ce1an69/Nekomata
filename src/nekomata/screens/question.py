from __future__ import annotations

from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Static


class QuestionScreen(Screen):
    DEFAULT_CSS = """
    QuestionScreen {
        align: center middle;
    }
    QuestionScreen #prompt {
        text-align: center;
        margin-bottom: 2;
    }
    QuestionScreen Input {
        width: 50;
        margin-bottom: 1;
    }
    QuestionScreen Button {
        width: 20;
        margin-bottom: 1;
    }
    """

    def __init__(self, spread_key: str) -> None:
        super().__init__()
        self.spread_key = spread_key

    def compose(self):
        with Center():
            yield Static("请输入你的问题：", id="prompt")
            with Vertical():
                yield Input(placeholder="例如：今天运势如何？", id="question-input")
                yield Button("🔮 开始抽牌", id="submit", variant="primary")
                yield Button("↩ 返回", id="back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id == "submit":
            inp = self.query_one("#question-input", Input)
            question = inp.value.strip() or "请为我指引方向。"
            self._go_to_reading(question)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "question-input":
            question = event.value.strip() or "请为我指引方向。"
            self._go_to_reading(question)

    def _go_to_reading(self, question: str) -> None:
        from nekomata.screens.reading import ReadingScreen
        self.app.question = question
        self.app.spread_key = self.spread_key
        self.app.push_screen(ReadingScreen(self.spread_key, question))
