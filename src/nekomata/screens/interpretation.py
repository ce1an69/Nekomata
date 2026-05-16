from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from rich.markdown import Markdown
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from nekomata.card.types import Reading
from nekomata.storage.journal import Journal


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
    ) -> None:
        super().__init__()
        self._interpretation = interpretation
        self._drawn_cards = drawn_cards
        self._question = question
        self._saved = False

    def compose(self):
        with Vertical():
            yield Static(Markdown(self._interpretation), id="interp-content")
            with Center(id="actions"):
                yield Button("💾 保存记录", id="save", variant="success")
                yield Button("🏠 返回首页", id="home")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "home":
            while len(self.app.screen_stack) > 1:
                self.app.pop_screen()
        elif event.button.id == "save" and not self._saved:
            reading = Reading(
                id=uuid4(),
                timestamp=datetime.now(),
                question=self._question,
                spread_name=self.app.spread_name,
                spread_name_zh=self.app.spread_name_zh,
                drawn_cards=self._drawn_cards,
                interpretation=self._interpretation,
            )
            journal = Journal(Path("data/journal.db"))
            journal.save(reading)
            self._saved = True
            save_btn = self.query_one("#save")
            save_btn.label = "已保存 ✓"
            save_btn.disabled = True
