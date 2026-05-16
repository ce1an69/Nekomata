from __future__ import annotations

from datetime import datetime
from pathlib import Path

from rich.markdown import Markdown
from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Static

from nekomata.card.types import Reading
from nekomata.storage.journal import Journal


class JournalScreen(Screen):
    DEFAULT_CSS = """
    JournalScreen {
        align: center top;
    }
    JournalScreen #reading-list {
        width: 1fr;
        height: 1fr;
    }
    JournalScreen #reading-detail {
        width: 1fr;
        height: 1fr;
        border: round $primary;
        padding: 1 2;
    }
    JournalScreen #back-bar {
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._readings: list[Reading] = []

    def compose(self) -> ComposeResult:
        with Horizontal(id="browser-area"):
            with VerticalScroll(id="reading-list"):
                pass
            with Vertical(id="reading-detail"):
                yield Static("选择一条记录查看详情", id="detail-placeholder")
        with Center(id="back-bar"):
            yield Button("↩ 返回", id="back")

    def on_mount(self) -> None:
        journal = Journal(Path("data/journal.db"))
        self._readings = journal.load_recent(20)
        self._show_readings()

    def _show_readings(self) -> None:
        container = self.query_one("#reading-list")
        container.remove_children()
        if not self._readings:
            container.mount(Static("暂无历史记录"))
            return
        for reading in self._readings:
            ts = reading.timestamp.strftime("%m-%d %H:%M")
            label = f"[{reading.spread_name_zh}] {ts} — {reading.question}"
            container.mount(ReadingItem(reading, label))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()


class ReadingItem(Static):
    def __init__(self, reading: Reading, label: str) -> None:
        self._reading = reading
        super().__init__(label)

    def on_click(self) -> None:
        detail_panel = self.app.screen.query_one("#reading-detail")
        detail_panel.remove_children()
        cards_info = "\n".join(
            f"- {dc.position.name_zh}：{dc.card.name_zh}{'（逆位）' if dc.is_reversed else ''}"
            for dc in self._reading.drawn_cards
        )
        content = (
            f"## {self._reading.question}\n"
            f"牌阵：{self._reading.spread_name_zh}\n"
            f"时间：{self._reading.timestamp.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"### 牌面\n{cards_info}\n\n"
            f"### 解读\n{self._reading.interpretation or '无'}"
        )
        detail_panel.mount(Static(Markdown(content)))
