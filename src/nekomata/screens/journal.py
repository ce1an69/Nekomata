"""Journal history screen for browsing past tarot readings."""


from uuid import UUID

from rich.markdown import Markdown
from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.events import Key
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Button, Static

from nekomata.card.types import Reading
from nekomata.screens.widgets import focus_sibling
from nekomata.storage.journal import Journal


class _ReadingItem(Static):
    """A focusable list item for a single past reading."""

    can_focus = True

    DEFAULT_CSS = """
    _ReadingItem {
        padding: 0 1;
        height: auto;
    }
    _ReadingItem:focus {
        background: #313244;
        color: #cba6f7;
        text-style: bold;
    }
    _ReadingItem:hover {
        background: #313244;
    }
    _ReadingItem.selected {
        background: #181825;
        border-left: tall #f9e2af;
    }
    _ReadingItem.selected:focus {
        background: #313244;
        color: #cba6f7;
        text-style: bold;
    }
    _ReadingItem.delete-pending {
        background: #302028;
        border-left: tall #f38ba8;
        color: #f38ba8;
    }
    _ReadingItem.delete-pending:focus {
        text-style: bold;
    }
    """

    def __init__(self, reading: Reading) -> None:
        self._reading = reading
        date = reading.timestamp.strftime("%Y-%m-%d %H:%M")
        label = reading.spread_name_zh or reading.spread_name
        n_rev = sum(1 for dc in reading.drawn_cards if dc.is_reversed)
        reversal = f" 逆位{n_rev}" if n_rev else ""
        n_cards = len(reading.drawn_cards)
        super().__init__(f"{date}  {label}（{n_cards}牌{reversal}）  —  {reading.question}")

    def on_click(self) -> None:
        self._show_detail()

    def on_focus(self) -> None:
        self._show_detail()

    def key_enter(self) -> None:
        self._show_detail()

    def _show_detail(self) -> None:
        """Show the full reading interpretation in the detail panel."""
        for item in self.screen.query(_ReadingItem):
            item.remove_class("selected")
        self.add_class("selected")
        detail = self.screen.query_one("#journal-detail")
        detail.remove_children()

        parts = []
        parts.append(f"**{self._reading.question}**\n")
        parts.append(
            f"{self._reading.spread_name_zh} · "
            f"{self._reading.timestamp.strftime('%Y-%m-%d %H:%M')}\n"
        )
        for dc in self._reading.drawn_cards:
            status = dc.status_label
            parts.append(f"- 【{dc.position.name_zh}】{dc.card.name_zh}（{status}）")
        if self._reading.interpretation:
            parts.append(f"\n---\n\n{self._reading.interpretation}")
        else:
            parts.append("\n\n*暂无解读内容*")

        detail.mount(Static(Markdown("\n".join(parts))))


class JournalScreen(Screen):
    """Browse saved tarot reading history."""

    BINDINGS = [
        ("d", "delete_reading", "删除"),
        ("escape", "go_back", "返回"),
    ]

    _DELETE_CONFIRM_TIMEOUT = 3.0

    DEFAULT_CSS = """
    JournalScreen {
        align: center top;
    }
    JournalScreen #journal-header {
        text-align: center;
        color: #a6adc8;
        margin: 1 0;
    }
    JournalScreen #journal-area {
        height: 1fr;
    }
    JournalScreen #journal-list {
        width: 1fr;
        height: 1fr;
    }
    JournalScreen #journal-detail {
        width: 1fr;
        height: 1fr;
        border: round #45475a;
        padding: 1 2;
    }
    JournalScreen #journal-actions {
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    JournalScreen Button {
        width: 24;
        margin: 0 1;
    }
    JournalScreen #hints {
        width: 100%;
        height: auto;
        color: #6c7086;
        text-align: center;
        margin-top: 1;
    }
    JournalScreen #empty-msg {
        color: #6c7086;
        text-align: center;
        margin: 2 0;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._readings: list[Reading] = []
        self._delete_target_id: UUID | None = None
        self._delete_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield Static("📖 占卜日记", id="journal-header")
        with Horizontal(id="journal-area"):
            with VerticalScroll(id="journal-list"):
                pass
            with Vertical(id="journal-detail"):
                yield Static("选择一条记录查看详情", id="detail-placeholder")
        with Center(id="journal-actions"):
            yield Button("↩ 返回", id="back")
        yield Static("↑↓ 浏览 · Tab 切换面板 · Enter 详情 · D 删除 · Esc 返回", id="hints")

    def on_mount(self) -> None:
        """Load recent readings and populate the list."""
        journal = Journal()
        self._readings = journal.list_recent(limit=50)
        count = journal.count()
        self.query_one("#journal-header", Static).update(f"📖 占卜日记（{count} 条）")
        self._populate_list()

    def on_unmount(self) -> None:
        """Stop delete confirmation timer when screen is removed."""
        if self._delete_timer is not None:
            self._delete_timer.stop()
            self._delete_timer = None

    def _focus_first(self) -> None:
        """Focus the first reading item in the list."""
        items = list(self.query(_ReadingItem))
        if items:
            items[0].focus()

    def _populate_list(self) -> None:
        """Fill the list container with reading items (or empty message)."""
        container = self.query_one("#journal-list")
        container.remove_children()

        if not self._readings:
            container.mount(Static("暂无保存的占卜记录", id="empty-msg"))
            return

        for reading in self._readings:
            container.mount(_ReadingItem(reading))

        self.set_timer(0.1, self._focus_first)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle back button click."""
        if event.button.id == "back":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        """Escape key binding — return to previous screen."""
        self.app.pop_screen()

    def action_delete_reading(self) -> None:
        """D key binding — delete the focused reading with confirm-on-repeat."""
        if not isinstance(self.focused, _ReadingItem):
            return
        reading = self.focused._reading

        # First press: show confirmation; second press within timeout: delete.
        if self._delete_target_id != reading.id:
            self._cancel_delete_confirm()
            self._delete_target_id = reading.id
            self.focused.add_class("delete-pending")
            self.query_one("#hints", Static).update(
                "⚠ 再按 D 确认删除 · 其他操作取消"
            )
            self._delete_timer = self.set_timer(
                self._DELETE_CONFIRM_TIMEOUT, self._cancel_delete_confirm
            )
            return

        # Confirmed — delete
        self._cancel_delete_confirm()
        journal = Journal()
        if journal.delete(reading.id):
            self._readings = [r for r in self._readings if r.id != reading.id]
            count = journal.count()
            self.query_one("#journal-header", Static).update(f"📖 占卜日记（{count} 条）")
            self._populate_list()
            detail = self.query_one("#journal-detail")
            detail.remove_children()
            detail.mount(Static("选择一条记录查看详情", id="detail-placeholder"))

    def _cancel_delete_confirm(self) -> None:
        """Reset the delete confirmation state and restore hints."""
        if self._delete_timer is not None:
            self._delete_timer.stop()
            self._delete_timer = None
        # Remove visual indicator from the pending item
        for item in self.query(_ReadingItem):
            item.remove_class("delete-pending")
        self._delete_target_id = None
        try:
            self.query_one("#hints", Static).update(
                "↑↓ 浏览 · Tab 切换面板 · Enter 详情 · D 删除 · Esc 返回"
            )
        except NoMatches:  # widget may not exist during unmount
            pass

    def key_down(self) -> None:
        if isinstance(self.focused, _ReadingItem):
            focus_sibling(self, _ReadingItem, 1)

    def key_up(self) -> None:
        if isinstance(self.focused, _ReadingItem):
            focus_sibling(self, _ReadingItem, -1)

    def key_tab(self, event: Key) -> None:
        """Cycle focus: reading list → back button → reading list."""
        event.stop()
        if isinstance(self.focused, _ReadingItem):
            btn = self.query_one("#back", Button)
            btn.focus()
        else:
            items = list(self.query(_ReadingItem))
            if items:
                items[0].focus()
