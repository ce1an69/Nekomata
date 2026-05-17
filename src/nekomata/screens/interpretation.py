"""Interpretation screen with typewriter animation."""

from rich.markdown import Markdown
from textual.app import ComposeResult
from textual.containers import Center, VerticalScroll
from textual.css.query import NoMatches
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Button, Static

from nekomata.card.types import DrawnCard
from nekomata.screens.widgets import go_home


class InterpretationScreen(Screen):
    """Displays AI-generated card interpretation with typewriter animation."""

    BINDINGS = [
        ("q", "go_home", "Home"),
        ("escape", "go_home", "Home"),
    ]

    DEFAULT_CSS = """
    InterpretationScreen {
        align: center top;
    }
    InterpretationScreen #interp-header {
        text-align: center;
        color: #cba6f7;
        text-style: bold;
        margin: 0 2 0 2;
    }
    InterpretationScreen #card-summary {
        text-align: center;
        color: #a6adc8;
        margin: 0 2;
    }
    InterpretationScreen #interp-divider {
        width: auto;
        height: 1;
        color: #585b70;
        text-align: center;
        margin: 0 2;
    }
    InterpretationScreen #interp-scroll {
        height: 1fr;
        border: round #313244;
        background: #181825;
        padding: 1 2;
        margin: 1 0 0 0;
    }
    InterpretationScreen #interp-content {
        margin: 0;
    }
    InterpretationScreen #actions {
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    InterpretationScreen #hints {
        width: 100%;
        height: auto;
        color: #6c7086;
        text-align: center;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        interpretation: str,
        drawn_cards: list[DrawnCard],
        question: str,
        spread_name: str = "",
        typewriter: bool = True,
    ) -> None:
        super().__init__()
        self._full_text = interpretation
        self._drawn_cards = drawn_cards
        self._question = question
        self._spread_name = spread_name
        self._typewriter = typewriter
        self._revealed_lines = 0
        self._lines: list[str] = interpretation.split("\n")
        self._tw_timer: Timer | None = None

    @property
    def _line_step(self) -> int:
        """Lines per tick — scales with text length for ~3s animation."""
        return max(1, len(self._lines) // 60)

    def compose(self) -> ComposeResult:
        header = self._question
        if self._spread_name:
            header += f"  ·  {self._spread_name}"
        yield Static(header, id="interp-header")
        if len(self._drawn_cards) <= 1:
            card_text = "  ".join(
                f"【{dc.position.name}】{dc.card.name}（{dc.status_label}）"
                for dc in self._drawn_cards
            )
        else:
            card_text = "\n".join(
                f"  【{dc.position.name}】{dc.card.name}（{dc.status_label}）"
                for dc in self._drawn_cards
            )
        yield Static(card_text, id="card-summary")
        yield Static("─── ✦ ───", id="interp-divider")
        with VerticalScroll(id="interp-scroll"):
            initial = "" if self._typewriter else self._full_text
            yield Static(Markdown(initial), id="interp-content")
        with Center(id="actions"):
            yield Button("Home", id="home")
        hint_text = "Space skip · Q home" if self._typewriter else "Q home"
        yield Static(hint_text, id="hints")

    def on_mount(self) -> None:
        """Start typewriter animation if enabled."""
        if self._typewriter and self._full_text:
            self._revealed_lines = 0
            self._tw_timer = self.set_interval(0.05, self._typewriter_tick)

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
            self.query_one("#hints", Static).update("Q home")
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

    def key_space(self) -> None:
        """Skip typewriter animation and show full text immediately."""
        if self._tw_timer is None:
            return
        self._tw_timer.stop()
        self._tw_timer = None
        self.query_one("#interp-content", Static).update(Markdown(self._full_text))
        self._revealed_lines = len(self._lines)
        self.query_one("#hints", Static).update("Q home")
        self._scroll_to_bottom()

    def action_go_home(self) -> None:
        """Escape binding — pop all screens back to home."""
        go_home(self)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle home button."""
        if event.button.id == "home":
            go_home(self)
