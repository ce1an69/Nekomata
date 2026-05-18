"""Interpretation screen with typewriter animation."""

from rich.markdown import Markdown
from textual.app import ComposeResult
from textual.containers import Center, VerticalScroll
from textual.css.scalar import ScalarOffset
from textual.css.query import NoMatches
from textual.geometry import Offset
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Button, Static

from nekomata.card.types import DrawnCard
from nekomata.screens.widgets import go_home


def _ease_in(widget, attr, target, duration):
    if attr == "offset" and isinstance(target, tuple):
        target = ScalarOffset.from_offset(Offset(*target))
    widget.styles.animate(attr, target, duration=duration, easing="out_cubic")


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
        transition: opacity 350ms out_cubic, offset 350ms out_cubic;
    }
    InterpretationScreen #card-summary {
        text-align: center;
        color: #a6adc8;
        margin: 0 2;
        transition: opacity 350ms out_cubic, offset 350ms out_cubic;
    }
    InterpretationScreen #interp-divider {
        width: auto;
        height: 1;
        color: #585b70;
        text-align: center;
        margin: 0 2;
        transition: opacity 400ms out_cubic;
    }
    InterpretationScreen #interp-scroll {
        height: 1fr;
        border: round #313244;
        background: #181825;
        padding: 1 2;
        margin: 1 0 0 0;
        transition: opacity 450ms out_cubic, offset 450ms out_cubic;
    }
    InterpretationScreen #interp-content {
        margin: 0;
        background: #181825;
    }
    InterpretationScreen #actions {
        align: center middle;
        height: auto;
        margin-top: 1;
        transition: opacity 320ms out_cubic;
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
        """Start entrance animation, then typewriter if enabled."""
        if self.app.animation_enabled:
            header = self.query_one("#interp-header")
            header.styles.opacity = 0
            header.styles.offset = (0, -1)
            _ease_in(header, "opacity", 1.0, 0.3)
            _ease_in(header, "offset", (0, 0), 0.3)

            summary = self.query_one("#card-summary")
            summary.styles.opacity = 0
            summary.styles.offset = (0, -1)
            self.set_timer(0.08, lambda: (
                _ease_in(summary, "opacity", 1.0, 0.28),
                _ease_in(summary, "offset", (0, 0), 0.28),
            ))

            scroll = self.query_one("#interp-scroll")
            scroll.styles.opacity = 0
            scroll.styles.offset = (0, 1)
            self.set_timer(0.18, lambda: (
                _ease_in(scroll, "opacity", 1.0, 0.35),
                _ease_in(scroll, "offset", (0, 0), 0.35),
            ))

            typewriter_delay = 0.4
        else:
            typewriter_delay = 0.0

        if self._typewriter and self._full_text:
            self._revealed_lines = 0
            self.set_timer(typewriter_delay, self._start_typewriter)

    def on_unmount(self) -> None:
        """Stop typewriter timer when screen is removed."""
        if self._tw_timer is not None:
            self._tw_timer.stop()
            self._tw_timer = None

    def _start_typewriter(self) -> None:
        """Begin the typewriter reveal interval."""
        if not self.is_mounted:
            return
        self._tw_timer = self.set_interval(0.05, self._typewriter_tick)

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

    def key_down(self) -> None:
        """Scroll interpretation down."""
        self.query_one("#interp-scroll", VerticalScroll).scroll_down(animate=True)

    def key_up(self) -> None:
        """Scroll interpretation up."""
        self.query_one("#interp-scroll", VerticalScroll).scroll_up(animate=True)

    def key_right(self) -> None:
        """Page interpretation down."""
        self.query_one("#interp-scroll", VerticalScroll).scroll_page_down(animate=True)

    def key_left(self) -> None:
        """Page interpretation up."""
        self.query_one("#interp-scroll", VerticalScroll).scroll_page_up(animate=True)

    def action_go_home(self) -> None:
        """Escape binding — pop all screens back to home."""
        go_home(self)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle home button."""
        if event.button.id == "home":
            go_home(self)
