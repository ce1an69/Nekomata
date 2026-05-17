"""Interpretation screen with typewriter animation and journal save."""

from rich.markdown import Markdown
from textual.app import ComposeResult
from textual.containers import Center, VerticalScroll
from textual.css.query import NoMatches
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Button, Static

from nekomata.card.types import DrawnCard, Reading
from nekomata.screens.widgets import go_home
from nekomata.storage.journal import Journal


class InterpretationScreen(Screen):
    """Displays AI-generated (or template) card interpretation with typewriter animation."""

    BINDINGS = [
        ("s", "save", "保存"),
        ("escape", "go_home", "返回首页"),
    ]

    DEFAULT_CSS = """
    InterpretationScreen {
        align: center top;
    }
    InterpretationScreen #interp-header {
        text-align: center;
        color: #cba6f7;
        text-style: bold;
        margin: 1 2 0 2;
    }
    InterpretationScreen #card-summary {
        text-align: center;
        color: #a6adc8;
        margin: 0 2;
    }
    InterpretationScreen #interp-divider {
        width: 100%;
        height: 1;
        color: #585b70;
        text-align: center;
        margin: 0 2;
    }
    InterpretationScreen #interp-scroll {
        height: 1fr;
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
    InterpretationScreen Button:disabled {
        color: #6c7086;
        border: tall #45475a;
    }
    InterpretationScreen #hints {
        width: 100%;
        height: auto;
        color: #6c7086;
        text-align: center;
        margin-top: 1;
    }
    InterpretationScreen #save-status {
        width: 100%;
        height: auto;
        color: #a6e3a1;
        text-align: center;
        margin-top: 0;
    }
    """

    def __init__(
        self,
        interpretation: str,
        drawn_cards: list[DrawnCard],
        question: str,
        spread_name: str = "",
        spread_name_zh: str = "",
        typewriter: bool = True,
    ) -> None:
        super().__init__()
        self._full_text = interpretation
        self._drawn_cards = drawn_cards
        self._question = question
        self._spread_name = spread_name
        self._spread_name_zh = spread_name_zh
        self._typewriter = typewriter
        self._revealed_lines = 0
        self._lines: list[str] = interpretation.split("\n")
        self._tw_timer: Timer | None = None
        self._saved = False

    @property
    def _line_step(self) -> int:
        """Lines per tick — scales with text length for ~3s animation.

        With a 50ms tick interval (20 ticks/sec), ~3s = ~60 ticks.
        step = total_lines / 60, clamped to at least 1.
        """
        return max(1, len(self._lines) // 60)

    def compose(self) -> ComposeResult:
        header = f"🔮 {self._question}"
        if self._spread_name_zh:
            header += f"  ·  {self._spread_name_zh}"
        yield Static(header, id="interp-header")
        # Single card: inline; multiple cards: one per line for readability
        if len(self._drawn_cards) <= 1:
            card_text = "  ".join(
                f"【{dc.position.name_zh}】{dc.card.name_zh}（{dc.status_label}）"
                for dc in self._drawn_cards
            )
        else:
            card_text = "\n".join(
                f"  【{dc.position.name_zh}】{dc.card.name_zh}（{dc.status_label}）"
                for dc in self._drawn_cards
            )
        yield Static(card_text, id="card-summary")
        yield Static("──── ✦ ────", id="interp-divider")
        with VerticalScroll(id="interp-scroll"):
            initial = "" if self._typewriter else self._full_text
            yield Static(Markdown(initial), id="interp-content")
        with Center(id="actions"):
            yield Button("💾 保存", id="save", variant="success")
            yield Button("🏠 返回首页", id="home")
        yield Static("", id="save-status")
        hint_text = "Space 跳过动画 · Esc 返回首页" if self._typewriter else "S 保存 · Esc 返回首页"
        yield Static(hint_text, id="hints")

    def on_mount(self) -> None:
        """Start typewriter animation if enabled."""
        if self._typewriter and self._full_text:
            self._revealed_lines = 0
            self._tw_timer = self.set_interval(0.05, self._typewriter_tick)
            # Disable save until typewriter completes
            self.query_one("#save", Button).disabled = True

    def on_unmount(self) -> None:
        """Stop typewriter timer when screen is removed."""
        if self._tw_timer is not None:
            self._tw_timer.stop()
            self._tw_timer = None

    def _typewriter_tick(self) -> None:
        """Advance the typewriter reveal by one step (line-based)."""
        self._revealed_lines += self._line_step
        if self._revealed_lines >= len(self._lines):
            self._revealed_lines = len(self._lines)
            self.query_one("#interp-content", Static).update(Markdown(self._full_text))
            if self._tw_timer is not None:
                self._tw_timer.stop()
                self._tw_timer = None
            self._enable_save()
            return
        visible = "\n".join(self._lines[: self._revealed_lines])
        self.query_one("#interp-content", Static).update(Markdown(visible))
        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        """Auto-scroll the interpretation content to the bottom."""
        try:
            scroll = self.query_one("#interp-scroll", VerticalScroll)
            scroll.scroll_end(animate=False)
        except NoMatches:
            pass

    def _enable_save(self) -> None:
        """Re-enable the save button and update hints after typewriter completes."""
        self.query_one("#save", Button).disabled = False
        self.query_one("#hints", Static).update("S 保存 · Esc 返回首页")

    def _skip_typewriter(self) -> None:
        """Immediately show the full interpretation text."""
        if self._tw_timer is not None:
            self._tw_timer.stop()
            self._tw_timer = None
        self.query_one("#interp-content", Static).update(Markdown(self._full_text))
        self._revealed_lines = len(self._lines)
        self._enable_save()
        self._scroll_to_bottom()

    def key_space(self) -> None:
        """Skip typewriter animation and show full text immediately."""
        self._skip_typewriter()

    def action_save(self) -> None:
        """S key binding — save the reading to journal."""
        self._do_save()

    def action_go_home(self) -> None:
        """Escape binding — pop all screens back to home."""
        go_home(self)

    def _do_save(self) -> None:
        """Save the reading to the journal database."""
        if self._saved:
            return
        reading = Reading(
            question=self._question,
            spread_name=self._spread_name,
            spread_name_zh=self._spread_name_zh,
            drawn_cards=self._drawn_cards,
            interpretation=self._full_text,
        )
        try:
            Journal().save(reading)
        except Exception:
            self.query_one("#save-status", Static).update("✗ 保存失败，请重试")
            return
        self._saved = True
        self.query_one("#save-status", Static).update("✓ 已保存到日记")
        save_btn = self.query_one("#save", Button)
        save_btn.disabled = True
        save_btn.label = "已保存"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle save and home buttons."""
        if event.button.id == "home":
            go_home(self)
        elif event.button.id == "save":
            self._do_save()
