from __future__ import annotations

from rich.markdown import Markdown
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static


class InterpretationScreen(Screen):
    DEFAULT_CSS = """
    InterpretationScreen {
        align: center top;
    }
    InterpretationScreen #interp-content {
        margin: 1 2;
    }
    InterpretationScreen #actions {
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    InterpretationScreen Button {
        width: 24;
        margin: 0 1;
    }
    """

    def __init__(
        self,
        interpretation: str,
        drawn_cards: list,
        question: str,
        typewriter: bool = True,
    ) -> None:
        super().__init__()
        self._full_text = interpretation
        self._drawn_cards = drawn_cards
        self._question = question
        self._typewriter = typewriter
        self._revealed = 0
        self._char_step = 3
        self._tw_timer = None

    def compose(self):
        with Vertical():
            initial = "" if self._typewriter else self._full_text
            yield Static(Markdown(initial), id="interp-content")
            with Center(id="actions"):
                yield Button("🏠 返回首页", id="home")

    def on_mount(self) -> None:
        if self._typewriter and self._full_text:
            self._revealed = 0
            self._tw_timer = self.set_interval(0.02, self._typewriter_tick)

    def _typewriter_tick(self) -> None:
        self._revealed += self._char_step
        if self._revealed >= len(self._full_text):
            self._revealed = len(self._full_text)
            content = self.query_one("#interp-content", Static)
            content.update(Markdown(self._full_text))
            if self._tw_timer is not None:
                self._tw_timer.stop()
                self._tw_timer = None
            return
        content = self.query_one("#interp-content", Static)
        content.update(Markdown(self._full_text[: self._revealed]))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "home":
            while len(self.app.screen_stack) > 1:
                self.app.pop_screen()
